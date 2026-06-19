from decimal import Decimal
import csv
from io import StringIO
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Address,
    AuditLog,
    Branch,
    ConstructionSite,
    Contract,
    Document,
    DocumentApproval,
    DocumentFile,
    InventoryItem,
    Invoice,
    Material,
    Notification,
    Payment,
    ProductionRequest,
    PurchaseOrder,
    Supplier,
    Ticket,
    User,
    Warehouse,
    StockMovement,
)
from .serializers import (
    AddressSerializer,
    AuditLogSerializer,
    BranchSerializer,
    ConstructionSiteSerializer,
    ContractSerializer,
    CustomTokenObtainPairSerializer,
    DocumentFileSerializer,
    DocumentSerializer,
    DocumentWorkflowSerializer,
    InventoryAdjustmentSerializer,
    InventoryItemSerializer,
    InvoiceSerializer,
    MaterialSerializer,
    NotificationSerializer,
    PaymentSerializer,
    ProductionRequestSerializer,
    PurchaseOrderItemSerializer,
    StockMovementSerializer,
    SupplierSerializer,
    TicketSerializer,
    UserRegisterSerializer,
    UserSerializer,
    WarehouseSerializer,
)


ADMIN_ROLES = {"admin"}
ARCHIVE_ROLES = {"admin", "procurement", "branch_manager"}
WORKFLOW_RULES = {
    "created": {"submit": {"next_status": "architecture", "roles": {"prorab", "procurement", "admin"}}},
    "architecture": {
        "approve": {"next_status": "ceo", "roles": {"architecture", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"architecture", "admin"}},
    },
    "ceo": {
        "approve": {"next_status": "approved", "roles": {"ceo", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"ceo", "admin"}},
    },
    "approved": {
        "advance": {"next_status": "contract", "roles": {"procurement", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"procurement", "admin"}},
    },
    "contract": {
        "advance": {"next_status": "payment", "roles": {"procurement", "accountant", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"procurement", "accountant", "admin"}},
    },
    "payment": {
        "advance": {"next_status": "delivering", "roles": {"accountant", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"accountant", "admin"}},
    },
    "delivering": {"advance": {"next_status": "received", "roles": {"warehouse", "admin"}}},
    "received": {"close": {"next_status": "closed", "roles": {"warehouse", "prorab", "admin"}}},
    "rejected": {"reopen": {"next_status": "created", "roles": {"admin", "procurement", "prorab"}}},
}


def is_admin(user):
    return user.is_staff or bool(ADMIN_ROLES.intersection(user.roles or []))


def branch_scope(queryset, user, field_name="branch"):
    if is_admin(user) or not user.branch_id:
        return queryset
    return queryset.filter(**{field_name: user.branch})


def filter_by_query_params(queryset, request, mapping):
    for param, field_name in mapping.items():
        value = request.query_params.get(param)
        if value:
            queryset = queryset.filter(**{field_name: value})
    return queryset


def build_document_number(doc_type):
    prefix_map = {
        "purchase_request": "XR",
        "contract": "SH",
        "invoice": "INV",
    }
    prefix = prefix_map.get(doc_type, "DOC")
    year = timezone.now().year
    count = Document.objects.filter(doc_type=doc_type, created_at__year=year).count() + 1
    return f"{prefix}-{year}-{count:04d}"


def create_audit_log(request, action, model_name, object_id=None, details=None):
    AuditLog.objects.create(
        user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details or {},
        ip_address=request.META.get("REMOTE_ADDR"),
    )


def notify_users(users, title, message, notification_type="info"):
    unique_users = []
    seen_ids = set()
    for user in users:
        if user and user.id not in seen_ids:
            unique_users.append(user)
            seen_ids.add(user.id)

    Notification.objects.bulk_create(
        [
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
            )
            for user in unique_users
        ]
    )


def notify_branch_roles(branch, roles, title, message, notification_type="info"):
    if not branch:
        return
    users = User.objects.filter(branch=branch, is_active=True)
    filtered = [user for user in users if is_admin(user) or bool(set(user.roles or []).intersection(roles))]
    if filtered:
        notify_users(filtered, title, message, notification_type)


def create_low_stock_notifications(item):
    threshold = item.min_quantity or Decimal("10")
    if item.quantity > threshold:
        return

    title = "Kam zaxira ogohlantirishi"
    message = f"{item.material.name} materiali {item.warehouse.name} omborida minimal chegaraga tushdi."
    notify_branch_roles(item.warehouse.branch, {"warehouse", "branch_manager", "admin"}, title, message, "warning")


def scoped_audit_logs(user):
    queryset = AuditLog.objects.select_related("user").order_by("-created_at")
    if is_admin(user) or not user.branch_id:
        return queryset

    return queryset.filter(
        Q(user__branch=user.branch)
        | Q(details__branch_id=user.branch_id)
    )


def export_to_csv(filename, fieldnames, rows):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT Token olish (login)."""

    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(APIView):
    """JWT Refresh token."""
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        try:
            refresh = RefreshToken(request.data['refresh'])
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            return Response(data, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except KeyError:
            return Response({'error': 'refresh token topilmadi'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout - tokenlarni blacklisted qilish."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserRegisterView(generics.CreateAPIView):
    """Ro'yxatdan o'tish."""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Welcome notification
        Notification.objects.create(
            user=user,
            title="E-Omborga xush kelibsiz!",
            message=f"Assalomu alaykum, {user.full_name}! E-Ombor tizimiga ro'yxatdan o'tdingiz.",
            notification_type='info'
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Foydalanuvchi profili."""
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        return self.request.user


class DashboardView(APIView):
    """Dashboard statistikalari."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        user = request.user

        documents = branch_scope(Document.objects.select_related("created_by", "site", "branch"), user)
        sites = branch_scope(ConstructionSite.objects.select_related("branch", "prorab"), user)
        warehouses = branch_scope(Warehouse.objects.select_related("branch"), user)
        inventory = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            user,
            "warehouse__branch",
        )
        tickets = branch_scope(
            Ticket.objects.select_related("created_by", "assigned_to", "branch", "site"),
            user,
        )
        invoices = branch_scope(
            Invoice.objects.select_related("document", "contract", "document__branch"),
            user,
            "document__branch",
        )

        payment_summary = invoices.aggregate(
            total_invoiced=Sum("total_amount"),
            total_paid=Sum("paid_amount"),
        )
        total_invoiced = payment_summary["total_invoiced"] or Decimal("0")
        total_paid = payment_summary["total_paid"] or Decimal("0")

        stats = {
            "total_documents": documents.count(),
            "pending_approvals": documents.filter(status__in=["architecture", "ceo"]).count(),
            "total_materials": Material.objects.count(),
            "total_warehouses": warehouses.count(),
            "total_sites": sites.count(),
            "low_stock_items": inventory.filter(
                Q(quantity__lte=Q(min_quantity)) | Q(min_quantity=0, quantity__lte=10)
            ).count(),
            "recent_documents": DocumentSerializer(documents.order_by("-created_at")[:5], many=True).data,
            "recent_tickets": TicketSerializer(tickets.order_by("-created_at")[:5], many=True).data,
            "notifications": NotificationSerializer(
                Notification.objects.filter(user=user).order_by("-created_at")[:10],
                many=True,
            ).data,
            "document_status_breakdown": list(
                documents.values("status").annotate(total=Count("id")).order_by("status")
            ),
            "payment_summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "remaining": total_invoiced - total_paid,
            },
            "site_budget_summary": {
                "total_budget": sites.aggregate(total=Sum("budget"))["total"] or Decimal("0"),
            },
        }

        return Response(stats, status=status.HTTP_200_OK)


class AnalyticsOverviewView(APIView):
    """Analytics va hisobotlar uchun agregatsiya endpointi."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        documents = branch_scope(Document.objects.select_related("branch", "site"), user)
        inventory = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            user,
            "warehouse__branch",
        )
        tickets = branch_scope(Ticket.objects.select_related("branch", "site"), user)
        invoices = branch_scope(
            Invoice.objects.select_related("document", "document__branch"),
            user,
            "document__branch",
        )
        audit_logs = scoped_audit_logs(user)

        overdue_invoices = invoices.filter(payment_status__in=["unpaid", "partial"], due_date__lt=timezone.localdate())
        low_stock_items = inventory.filter(Q(quantity__lte=Q(min_quantity)) | Q(min_quantity=0, quantity__lte=10))

        data = {
            "documents_by_type": list(documents.values("doc_type").annotate(total=Count("id")).order_by("doc_type")),
            "documents_by_status": list(documents.values("status").annotate(total=Count("id")).order_by("status")),
            "tickets_by_priority": list(tickets.values("priority").annotate(total=Count("id")).order_by("priority")),
            "tickets_by_status": list(tickets.values("status").annotate(total=Count("id")).order_by("status")),
            "overdue_invoices": InvoiceSerializer(overdue_invoices.order_by("due_date")[:10], many=True).data,
            "low_stock_items": InventoryItemSerializer(low_stock_items.order_by("quantity")[:10], many=True).data,
            "recent_audit_logs": AuditLogSerializer(audit_logs[:10], many=True).data,
        }
        return Response(data, status=status.HTTP_200_OK)


# --- Document Views ---
class DocumentListCreateView(generics.ListCreateAPIView):
    """Hujjatlar ro'yxati va yaratish."""
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        queryset = branch_scope(
            Document.objects.select_related("created_by", "site", "branch").prefetch_related("approvals"),
            user,
        ).order_by("-created_at")
        archived_filter = self.request.query_params.get("archived", "false")
        if archived_filter == "true":
            queryset = queryset.filter(is_archived=True)
        elif archived_filter != "all":
            queryset = queryset.filter(is_archived=False)
        queryset = filter_by_query_params(
            queryset,
            self.request,
            {"status": "status", "doc_type": "doc_type", "site": "site_id"},
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(doc_number__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        site = serializer.validated_data.get("site")
        branch = site.branch if site else self.request.user.branch
        if site and not is_admin(self.request.user) and self.request.user.branch_id and site.branch_id != self.request.user.branch_id:
            raise serializers.ValidationError("Siz faqat o'z filiali obyektiga hujjat yarata olasiz")
        document = serializer.save(
            created_by=self.request.user,
            branch=branch,
            doc_number=build_document_number(serializer.validated_data["doc_type"]),
        )
        create_audit_log(
            self.request,
            "document_created",
            "Document",
            document.id,
            {"doc_number": document.doc_number, "status": document.status},
        )
        notify_branch_roles(
            branch,
            {"architecture", "branch_manager", "admin"},
            "Yangi hujjat yaratildi",
            f"{document.doc_number} raqamli hujjat yaratildi va ko'rib chiqishni kutmoqda.",
            "info",
        )


class DocumentWorkflowActionView(APIView):
    """Hujjat workflow amallari."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        serializer = DocumentWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = branch_scope(
            Document.objects.select_related("created_by", "branch", "site"),
            request.user,
        ).filter(pk=pk).first()
        if not document:
            return Response({"error": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        action = serializer.validated_data["action"]
        comment = serializer.validated_data.get("comment", "").strip()
        rule = WORKFLOW_RULES.get(document.status, {}).get(action)
        if not rule:
            return Response({"error": "Bu holatda ushbu amal mavjud emas"}, status=status.HTTP_400_BAD_REQUEST)

        if not (is_admin(request.user) or bool(set(request.user.roles or []).intersection(rule["roles"]))):
            return Response({"error": "Bu amal uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        if action == "reject" and not comment:
            return Response({"error": "Rad etishda sabab kiritish majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        previous_status = document.status
        document.status = rule["next_status"]
        document.save(update_fields=["status", "updated_at"])

        DocumentApproval.objects.create(
            document=document,
            approver=request.user,
            action=action,
            comment=comment,
        )
        create_audit_log(
            request,
            "document_workflow_changed",
            "Document",
            document.id,
            {"from": previous_status, "to": document.status, "action": action, "comment": comment},
        )

        recipients = [document.created_by]
        notify_branch_roles(
            document.branch,
            {"procurement", "accountant", "warehouse", "branch_manager", "admin"},
            "Hujjat holati yangilandi",
            f"{document.doc_number} hujjati {previous_status} dan {document.status} ga o'tdi.",
            "info" if document.status != "rejected" else "warning",
        )
        if recipients:
            notify_users(
                recipients,
                "Hujjat holati yangilandi",
                f"{document.doc_number} hujjatingizning yangi holati: {document.get_status_display()}",
                "info" if document.status != "rejected" else "warning",
            )

        return Response(DocumentSerializer(document, context={"request": request}).data, status=status.HTTP_200_OK)


class DocumentArchiveToggleView(APIView):
    """Hujjatni arxivlash yoki arxivdan chiqarish."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        document = branch_scope(
            Document.objects.select_related("created_by", "branch", "site"),
            request.user,
        ).filter(pk=pk).first()
        if not document:
            return Response({"error": "Hujjat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        if not (is_admin(request.user) or bool(set(request.user.roles or []).intersection(ARCHIVE_ROLES))):
            return Response({"error": "Arxivlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        archive = request.data.get("archive", True)
        if isinstance(archive, str):
            archive = archive.lower() == "true"

        document.is_archived = archive
        document.archived_at = timezone.now() if archive else None
        document.save(update_fields=["is_archived", "archived_at", "updated_at"])

        create_audit_log(
            request,
            "document_archived" if archive else "document_unarchived",
            "Document",
            document.id,
            {
                "doc_number": document.doc_number,
                "is_archived": document.is_archived,
                "branch_id": document.branch_id,
            },
        )
        return Response(DocumentSerializer(document, context={"request": request}).data, status=status.HTTP_200_OK)


class DocumentsExportView(APIView):
    """Hujjatlarni CSV eksport qilish."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        queryset = branch_scope(
            Document.objects.select_related("created_by", "site", "branch"),
            request.user,
        ).order_by("-created_at")

        archived_filter = request.query_params.get("archived", "all")
        if archived_filter == "true":
            queryset = queryset.filter(is_archived=True)
        elif archived_filter == "false":
            queryset = queryset.filter(is_archived=False)

        queryset = filter_by_query_params(
            queryset,
            request,
            {"status": "status", "doc_type": "doc_type", "site": "site_id"},
        )

        rows = [
            {
                "doc_number": document.doc_number,
                "doc_type": document.get_doc_type_display(),
                "status": document.get_status_display(),
                "title": document.title,
                "branch": document.branch.name if document.branch else "",
                "site": document.site.name if document.site else "",
                "created_by": document.created_by.full_name if document.created_by else "",
                "total_amount": document.total_amount,
                "is_archived": "Ha" if document.is_archived else "Yo'q",
                "created_at": timezone.localtime(document.created_at).strftime("%Y-%m-%d %H:%M"),
            }
            for document in queryset
        ]
        return export_to_csv(
            "documents-export.csv",
            [
                "doc_number",
                "doc_type",
                "status",
                "title",
                "branch",
                "site",
                "created_by",
                "total_amount",
                "is_archived",
                "created_at",
            ],
            rows,
        )


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Hujjat tahrirlash va o'chirish."""
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return branch_scope(
            Document.objects.select_related("created_by", "site", "branch").prefetch_related("approvals"),
            self.request.user,
        ).order_by("-created_at")


# --- Purchase Order Views ---
class PurchaseOrderListView(generics.ListAPIView):
    """Xarid buyurtmalari ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        user = request.user
        orders = PurchaseOrder.objects.select_related(
            'document', 'supplier'
        ).prefetch_related('items__material').order_by('-document__created_at')
        
        if user.branch:
            orders = orders.filter(document__branch=user.branch)
        
        data = []
        for order in orders:
            data.append({
                'id': order.id,
                'doc_number': order.document.doc_number,
                'title': order.document.title,
                'status': order.document.status,
                'total_amount': order.document.total_amount,
                'supplier': order.supplier.name if order.supplier else None,
                'items': PurchaseOrderItemSerializer(order.items.all(), many=True).data,
                'created_at': order.document.created_at,
            })
        
        return Response({'results': data}, status=status.HTTP_200_OK)


# --- Material Views ---
class MaterialListView(generics.ListCreateAPIView):
    """Materiallar ro'yxati va yaratish."""
    serializer_class = MaterialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Material.objects.all()


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Material tahrirlash va o'chirish."""
    serializer_class = MaterialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Material.objects.all()


# --- Warehouse Views ---
class WarehouseListView(generics.ListCreateAPIView):
    """Omborxonalar ro'yxati va yaratish."""
    serializer_class = WarehouseSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Warehouse.objects.select_related("branch").all()

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user)


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Omborxona tahrirlash va o'chirish."""
    serializer_class = WarehouseSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Warehouse.objects.select_related("branch").all()


# --- Inventory Views ---
class InventoryListView(generics.ListCreateAPIView):
    """Ombor zaxiralari ro'yxati."""
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        queryset = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            self.request.user,
            "warehouse__branch",
        ).order_by("material__name")
        return filter_by_query_params(
            queryset,
            self.request,
            {"warehouse": "warehouse_id", "material": "material_id"},
        )

    def perform_create(self, serializer):
        warehouse = serializer.validated_data["warehouse"]
        quantity = serializer.validated_data.get("quantity", Decimal("0"))
        if not is_admin(self.request.user) and self.request.user.branch_id and warehouse.branch_id != self.request.user.branch_id:
            raise serializers.ValidationError("Siz faqat o'z filiali ombori uchun yozuv yarata olasiz")

        item = serializer.save()
        if quantity > 0:
            StockMovement.objects.create(
                warehouse=item.warehouse,
                material=item.material,
                movement_type="IN",
                quantity=quantity,
                performed_by=self.request.user,
                notes="Boshlang'ich zaxira yaratildi",
            )
        create_audit_log(
            self.request,
            "inventory_created",
            "InventoryItem",
            item.id,
            {
                "warehouse_id": item.warehouse_id,
                "material_id": item.material_id,
                "quantity": str(item.quantity),
                "branch_id": item.warehouse.branch_id,
            },
        )
        create_low_stock_notifications(item)


class InventoryUpdateView(APIView):
    """Ombor zaxirasini yangilash."""
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        item = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            request.user,
            "warehouse__branch",
        ).filter(pk=pk).first()
        if not item:
            return Response({"error": "Zaxira topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = InventoryAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity_delta = serializer.validated_data.get("quantity_delta", Decimal("0"))
        min_quantity = serializer.validated_data.get("min_quantity")
        notes = serializer.validated_data.get("notes", "")

        new_quantity = item.quantity + quantity_delta
        if new_quantity < 0:
            return Response({"error": "Miqdor manfiy bo'lib qolmasligi kerak"}, status=status.HTTP_400_BAD_REQUEST)

        item.quantity = new_quantity
        if min_quantity is not None:
            item.min_quantity = min_quantity
        item.save()

        if quantity_delta != 0:
            StockMovement.objects.create(
                warehouse=item.warehouse,
                material=item.material,
                movement_type="IN" if quantity_delta > 0 else "OUT",
                quantity=abs(quantity_delta),
                performed_by=request.user,
                notes=notes,
            )

        create_low_stock_notifications(item)
        create_audit_log(
            request,
            "inventory_adjusted",
            "InventoryItem",
            item.id,
            {"quantity_delta": str(quantity_delta), "new_quantity": str(item.quantity), "notes": notes},
        )

        return Response(InventoryItemSerializer(item).data, status=status.HTTP_200_OK)


class StockMovementListView(generics.ListAPIView):
    """Materiallar harakati tarixi."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        queryset = branch_scope(
            StockMovement.objects.select_related("warehouse", "warehouse__branch", "material", "performed_by"),
            self.request.user,
            "warehouse__branch",
        ).order_by("-performed_at")
        return filter_by_query_params(
            queryset,
            self.request,
            {"warehouse": "warehouse_id", "material": "material_id", "movement_type": "movement_type"},
        )


class InventoryExportView(APIView):
    """Inventory ni CSV eksport qilish."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        queryset = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            request.user,
            "warehouse__branch",
        ).order_by("warehouse__name", "material__name")
        queryset = filter_by_query_params(
            queryset,
            request,
            {"warehouse": "warehouse_id", "material": "material_id"},
        )

        rows = [
            {
                "warehouse": item.warehouse.name,
                "branch": item.warehouse.branch.name if item.warehouse.branch else "",
                "material_code": item.material.code,
                "material_name": item.material.name,
                "quantity": item.quantity,
                "min_quantity": item.min_quantity,
                "is_low_stock": "Ha" if item.quantity <= (item.min_quantity or Decimal("10")) else "Yo'q",
                "updated_at": timezone.localtime(item.updated_at).strftime("%Y-%m-%d %H:%M"),
            }
            for item in queryset
        ]
        return export_to_csv(
            "inventory-export.csv",
            ["warehouse", "branch", "material_code", "material_name", "quantity", "min_quantity", "is_low_stock", "updated_at"],
            rows,
        )


# --- Construction Site Views ---
class ConstructionSiteListView(generics.ListCreateAPIView):
    """Qurilish obyektlari ro'yxati va yaratish."""
    serializer_class = ConstructionSiteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = ConstructionSite.objects.all()
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        qs = branch_scope(qs.select_related("branch", "prorab"), user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(branch=serializer.validated_data.get("branch") or self.request.user.branch)


class ConstructionSiteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Qurilish obyekti tahrirlash va o'chirish."""
    serializer_class = ConstructionSiteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = ConstructionSite.objects.all()


# --- Branch Views ---
class BranchListView(generics.ListCreateAPIView):
    """Filiallar ro'yxati."""
    serializer_class = BranchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Branch.objects.all().order_by("name")


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Filial tahrirlash va o'chirish."""
    serializer_class = BranchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Branch.objects.all()


# --- Supplier Views ---
class SupplierListView(generics.ListCreateAPIView):
    """Etkazib beruvchilar ro'yxati."""
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Supplier.objects.all().order_by("name")


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Etkazib beruvchi tahrirlash va o'chirish."""
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Supplier.objects.all()


# --- Notification Views ---
class NotificationListView(generics.ListAPIView):
    """Bildirishnomalar ro'yxati."""
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationMarkReadView(generics.UpdateAPIView):
    """Bildirishnomani o'qilgan deb belgilash."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, pk=None):
        notification = Notification.objects.filter(
            user=request.user, id=pk
        ).first()
        if notification:
            notification.is_read = True
            notification.save()
            return Response({'message': 'O\'qilgan deb belgilandi'})
        return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllReadView(APIView):
    """Barcha bildirishnomalarni o'qilgan deb belgilash."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Barcha bildirishnomalar o\'qilgan deb belgilandi'})


class AuditLogListView(generics.ListAPIView):
    """Audit log ro'yxati."""

    serializer_class = AuditLogSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = scoped_audit_logs(self.request.user)
        queryset = filter_by_query_params(
            queryset,
            self.request,
            {"action": "action", "model_name": "model_name", "user": "user_id"},
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(action__icontains=search)
                | Q(model_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset


# --- Address Views ---
class AddressListView(generics.ListCreateAPIView):
    """Manzillar ro'yxati."""
    serializer_class = AddressSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Address.objects.all()


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manzil tahrirlash va o'chirish."""
    serializer_class = AddressSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Address.objects.all()


# --- Document File Views ---
class DocumentFileListView(generics.ListAPIView):
    """Hujjat fayllari ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DocumentFileSerializer
    
    def get_queryset(self):
        doc_id = self.kwargs.get('doc_pk')
        return branch_scope(
            DocumentFile.objects.select_related("document", "uploaded_by", "document__branch"),
            self.request.user,
            "document__branch",
        ).filter(document_id=doc_id).order_by("-created_at")


class DocumentFileUploadView(APIView):
    """Hujjatga fayl yuklash."""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, doc_pk):
        document = Document.objects.filter(id=doc_pk).first()
        if not document:
            return Response({'error': 'Hujjat topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Fayl tanlanmadi'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Max 10MB
        if file.size > 10 * 1024 * 1024:
            return Response({'error': 'Fayl hajmi 10MB dan oshmasligi kerak'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_extensions = {".pdf", ".xlsx", ".xls", ".jpg", ".jpeg", ".png"}
        suffix = ""
        if "." in file.name:
            suffix = file.name[file.name.rfind("."):].lower()
        if suffix not in allowed_extensions:
            return Response(
                {"error": "Faqat PDF, XLSX, XLS, JPG, JPEG va PNG fayllariga ruxsat beriladi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = DocumentFile.objects.create(
            document=document,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            uploaded_by=request.user
        )

        create_audit_log(
            request,
            "document_file_uploaded",
            "DocumentFile",
            created.id,
            {"document_id": document.id, "filename": file.name},
        )
        return Response({'message': 'Fayl muvaffaqiyatli yuklandi'}, status=status.HTTP_201_CREATED)


# --- Contract Views ---
class ContractListView(generics.ListAPIView):
    """Shartnomalar ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer
    
    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")


class ContractDetailView(generics.RetrieveAPIView):
    """Shartnoma tafsilotlari."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer
    
    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")


# --- Invoice Views ---
class InvoiceListView(generics.ListCreateAPIView):
    """Hisob-fakturalar ro'yxati."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Invoice.objects.select_related("document", "contract", "document__branch").order_by("-invoice_date")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user, "document__branch")


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    """Hisob-faktura tafsilotlari."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Invoice.objects.select_related("document", "contract", "document__branch").order_by("-invoice_date")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user, "document__branch")


# --- Payment Views ---
class PaymentListView(generics.ListAPIView):
    """To'lovlar ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return branch_scope(
            Payment.objects.select_related("invoice", "invoice__document", "invoice__document__branch", "performed_by"),
            self.request.user,
            "invoice__document__branch",
        ).order_by("-payment_date")


class PaymentCreateView(generics.CreateAPIView):
    """To'lov yaratish."""
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def perform_create(self, serializer):
        invoice_id = self.kwargs.get('invoice_pk')
        invoice = branch_scope(
            Invoice.objects.select_related("document", "document__branch"),
            self.request.user,
            "document__branch",
        ).filter(id=invoice_id).first()
        if not invoice:
            raise serializers.ValidationError("Hisob-faktura topilmadi")

        amount = serializer.validated_data["amount"]
        if amount <= 0:
            raise serializers.ValidationError("To'lov summasi 0 dan katta bo'lishi kerak")
        if invoice.paid_amount + amount > invoice.total_amount:
            raise serializers.ValidationError("To'lov invoice summasidan oshib ketdi")

        payment = serializer.save(invoice=invoice, performed_by=self.request.user)

        invoice.paid_amount += payment.amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = "paid"
        elif invoice.paid_amount > 0:
            invoice.payment_status = "partial"
        invoice.save()

        create_audit_log(
            self.request,
            "payment_created",
            "Payment",
            payment.id,
            {"invoice": invoice.invoice_number, "amount": str(payment.amount)},
        )
        notify_users(
            [invoice.document.created_by],
            "Invoice bo'yicha to'lov qayd etildi",
            f"{invoice.invoice_number} uchun {payment.amount} summa to'landi.",
            "success",
        )


# --- Production Request Views ---
class ProductionRequestListView(generics.ListCreateAPIView):
    """Ishlab chiqarish zayavkalari ro'yxati."""
    serializer_class = ProductionRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return branch_scope(
            ProductionRequest.objects.select_related("site", "site__branch", "created_by"),
            self.request.user,
            "site__branch",
        ).order_by("-created_at")
    
    def perform_create(self, serializer):
        today = timezone.now().strftime('%Y%m%d')
        count = ProductionRequest.objects.filter(
            created_at__date=timezone.localdate()
        ).count() + 1
        serializer.save(
            created_by=self.request.user,
            request_number=f"PR-{today}-{count:04d}"
        )


class ProductionRequestDetailView(generics.RetrieveUpdateAPIView):
    """Ishlab chiqarish zayavka tafsilotlari."""
    serializer_class = ProductionRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return branch_scope(
            ProductionRequest.objects.select_related("site", "site__branch", "created_by"),
            self.request.user,
            "site__branch",
        ).order_by("-created_at")


# --- Ticket Views ---
class TicketListView(generics.ListCreateAPIView):
    """Murojaatlar ro'yxati."""
    serializer_class = TicketSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related(
            'created_by', 'assigned_to', 'branch', 'site'
        ).order_by('-created_at')
        
        if user.is_staff or 'admin' in user.roles:
            return qs
        
        if user.branch:
            qs = qs.filter(branch=user.branch)
        else:
            qs = qs.filter(created_by=user)

        return filter_by_query_params(
            qs,
            self.request,
            {"status": "status", "priority": "priority", "category": "category"},
        )
    
    def perform_create(self, serializer):
        site = serializer.validated_data.get("site")
        if site and not is_admin(self.request.user) and self.request.user.branch_id and site.branch_id != self.request.user.branch_id:
            raise serializers.ValidationError("Siz faqat o'z filiali obyektiga murojaat yarata olasiz")

        ticket = serializer.save(
            created_by=self.request.user,
            branch=serializer.validated_data.get("branch") or (site.branch if site else self.request.user.branch),
        )
        create_audit_log(
            self.request,
            "ticket_created",
            "Ticket",
            ticket.id,
            {
                "branch_id": ticket.branch_id,
                "priority": ticket.priority,
                "status": ticket.status,
            },
        )
        notify_branch_roles(
            ticket.branch,
            {"branch_manager", "admin"},
            "Yangi murojaat yaratildi",
            f"{ticket.title} nomli murojaat yaratildi.",
            "info",
        )


class TicketDetailView(generics.RetrieveUpdateAPIView):
    """Murojaat tafsilotlari."""
    serializer_class = TicketSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related(
            'created_by', 'assigned_to', 'branch', 'site'
        ).order_by('-created_at')
        
        if user.is_staff or 'admin' in user.roles:
            return qs
        
        if user.branch:
            return qs.filter(branch=user.branch)
        
        return qs.filter(created_by=user)


class TicketsExportView(APIView):
    """Murojaatlarni CSV eksport qilish."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        queryset = Ticket.objects.select_related("created_by", "assigned_to", "branch", "site").order_by("-created_at")

        if not is_admin(user):
            if user.branch_id:
                queryset = queryset.filter(branch=user.branch)
            else:
                queryset = queryset.filter(created_by=user)

        queryset = filter_by_query_params(
            queryset,
            request,
            {"status": "status", "priority": "priority", "category": "category"},
        )

        rows = [
            {
                "title": ticket.title,
                "category": ticket.get_category_display(),
                "priority": ticket.get_priority_display(),
                "status": ticket.get_status_display(),
                "branch": ticket.branch.name if ticket.branch else "",
                "site": ticket.site.name if ticket.site else "",
                "created_by": ticket.created_by.full_name if ticket.created_by else "",
                "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else "",
                "created_at": timezone.localtime(ticket.created_at).strftime("%Y-%m-%d %H:%M"),
            }
            for ticket in queryset
        ]
        return export_to_csv(
            "tickets-export.csv",
            ["title", "category", "priority", "status", "branch", "site", "created_by", "assigned_to", "created_at"],
            rows,
        )
