from decimal import Decimal
import csv
from io import StringIO
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import F, Q, Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import exceptions, generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
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
    PurchaseOrderCreateSerializer,
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderUpdateSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
    SupplierSerializer,
    TicketSerializer,
    UserCreateSerializer,
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    WarehouseSerializer,
)
from .workflow import WORKFLOW_RULES


ADMIN_ROLES = {"admin"}
# Tashkilot bo'ylab ko'radigan rollar. Bu FAQAT ko'rish doirasi — yozish
# huquqi quyidagi alohida to'plamlar bilan tekshiriladi va bu yerga bog'liq
# emas. CEO va xaridlar bo'limi barcha filiallar bo'yicha qaror qabul qiladi,
# nazorat roli esa butun tizimni ko'rmasa vazifasini bajara olmaydi.
GLOBAL_SCOPE_ROLES = {"admin", "ceo", "procurement", "anticorruption"}
ARCHIVE_ROLES = {"admin", "procurement", "branch_manager"}
STOCK_MOVEMENT_ROLES = {"admin", "warehouse"}
# Filial rahbari so'rovni o'zi to'ldiradi — material qatorlarisiz so'rovning
# mazmuni bo'lmaydi.
PURCHASE_ORDER_ROLES = {"admin", "procurement", "branch_manager"}
CONTRACT_ROLES = {"admin", "procurement"}
SUPPLIER_ROLES = {"admin", "procurement"}
INVOICE_ROLES = {"admin", "accountant", "procurement"}
PAYMENT_ROLES = {"admin", "accountant"}
SITE_ROLES = {"admin", "branch_manager", "architecture"}
DOCUMENT_MANAGE_ROLES = {"admin", "procurement", "branch_manager"}


def is_admin(user):
    return user.is_staff or bool(ADMIN_ROLES.intersection(user.roles or []))


def has_any_role(user, roles):
    return is_admin(user) or bool(set(user.roles or []).intersection(roles))


class RoleGatedWrite(permissions.BasePermission):
    """
    O'qish hammaga (autentifikatsiyadan o'tganlarga), yozish esa faqat
    `write_roles` dagi rollarga ochiq.

    Ma'lumotnoma bazasi — filial, material, ombor, obyekt, yetkazib beruvchi —
    ilgari hech qanday rol tekshiruvisiz edi: istalgan xodim material qo'sha,
    ombor tahrirlay yoki filialni butunlay o'chira olardi (filial o'chsa unga
    bog'langan foydalanuvchilar filialsiz qolardi).
    """

    write_roles = ADMIN_ROLES
    message = "Bu bo'limni o'zgartirish uchun sizda ruxsat yo'q"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return has_any_role(request.user, self.write_roles)


class AdminOnlyWrite(RoleGatedWrite):
    write_roles = ADMIN_ROLES


class SupplierWrite(RoleGatedWrite):
    write_roles = SUPPLIER_ROLES
    message = "Yetkazib beruvchini o'zgartirish uchun sizda ruxsat yo'q"


class SiteWrite(RoleGatedWrite):
    write_roles = SITE_ROLES
    message = "Qurilish obyektini o'zgartirish uchun sizda ruxsat yo'q"


class InvoiceWrite(RoleGatedWrite):
    write_roles = INVOICE_ROLES
    message = "Hisob-fakturani o'zgartirish uchun sizda ruxsat yo'q"


class PaymentWrite(RoleGatedWrite):
    write_roles = PAYMENT_ROLES
    message = "To'lov qayd etish uchun sizda ruxsat yo'q"


def can_manage_stock(user):
    """Zaxira o'zgartiradigan har qanday amal — faqat omborchi va admin."""
    return is_admin(user) or bool(set(user.roles or []).intersection(STOCK_MOVEMENT_ROLES))


def branch_scope(queryset, user, field_name="branch"):
    """
    Natijani foydalanuvchi filiali bilan cheklaydi.

    Filialsiz foydalanuvchi bo'sh natija oladi. Ilgari bu holat filtrni
    butunlay o'chirar edi, ya'ni `/auth/register/` orqali ochilgan yangi
    hisob (filiali yo'q) barcha filiallarning hujjatlari, shartnomalari va
    to'lovlarini ko'ra olardi.

    `GLOBAL_SCOPE_ROLES` — istisno: markaziy rollar (rais, xaridlar, nazorat)
    barcha filiallarni ko'radi. Ular ko'pincha filialga biriktirilmaydi, va
    bu istisnosiz filialsiz hisob sifatida hech nima ko'rmay qolardi.
    """
    if is_admin(user) or set(user.roles or []) & GLOBAL_SCOPE_ROLES:
        return queryset
    if not user.branch_id:
        return queryset.none()
    return queryset.filter(**{field_name: user.branch})


def filter_by_query_params(queryset, request, mapping):
    for param, field_name in mapping.items():
        value = request.query_params.get(param)
        if value:
            queryset = queryset.filter(**{field_name: value})
    return queryset


def next_sequence_number(queryset, field_name, prefix):
    """
    `prefix` bilan boshlanadigan eng katta raqamdan keyingisini qaytaradi.

    Ilgari raqam `count() + 1` bilan yig'ilardi. Bitta yozuv o'chirilishi
    bilan sanoq orqaga qaytar va keyingi yozuv allaqachon band raqamni
    so'rar edi — unique cheklovi buzilib, foydalanuvchi 500 olardi. Mavjud
    eng katta qiymatdan hisoblash raqamni faqat oldinga suradi.
    """
    highest = 0
    existing = queryset.filter(**{f"{field_name}__startswith": prefix}).values_list(
        field_name, flat=True
    )
    for value in existing:
        tail = value[len(prefix):]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return highest + 1


def build_document_number(doc_type):
    prefix_map = {
        "purchase_request": "XR",
        "contract": "SH",
        "invoice": "INV",
    }
    prefix = f"{prefix_map.get(doc_type, 'DOC')}-{timezone.now().year}-"
    return f"{prefix}{next_sequence_number(Document.objects, 'doc_number', prefix):04d}"


def save_with_unique_number(save):
    """
    `save(...)` ni raqam to'qnashuvida qayta chaqiradi.

    Raqam o'qish va yozish o'rtasida boshqa so'rov o'sha raqamni band qilib
    ulgurishi mumkin. Bunda IntegrityError qaytadi — qayta urinish yangi
    raqamni oladi.
    """
    last_error = None
    for _ in range(5):
        try:
            with transaction.atomic():
                return save()
        except IntegrityError as exc:
            last_error = exc
    raise last_error


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
    """
    Filialdagi tegishli rollarga xabar yuboradi.

    Markaziy rollar (rais, xaridlar, nazorat) ko'pincha filialga biriktirilmaydi
    — ular filial bo'yicha filtrda umuman topilmasdi va zanjirdagi o'z
    navbatlarini xabarsiz kutib qolardi. Shuning uchun ular filialdan qat'i
    nazar qo'shiladi.
    """
    if not branch:
        return

    wanted = set(roles)
    # `roles` — JSONField, uni bazada ishonchli filtrlab bo'lmaydi (SQLite va
    # PostgreSQL da sintaksis boshqacha), shuning uchun saralash Python'da.
    # Ichki tizim, foydalanuvchilar soni kichik — bu qabul qilinadigan narx.
    filtered = [
        user
        for user in User.objects.filter(is_active=True).only("id", "roles", "branch", "is_staff")
        if is_admin(user)
        or (
            bool(set(user.roles or []) & wanted)
            and (user.branch_id == branch.id or bool(set(user.roles or []) & GLOBAL_SCOPE_ROLES))
        )
    ]
    if filtered:
        notify_users(filtered, title, message, notification_type)


class InsufficientStockError(Exception):
    """Omborda yetarli qoldiq bo'lmaganda ko'tariladi."""


def lock_inventory_item(warehouse, material, create_if_missing=False):
    """InventoryItem ni satr darajasida qulflab qaytaradi (transaction ichida chaqirilsin)."""
    item = InventoryItem.objects.select_for_update().filter(warehouse=warehouse, material=material).first()
    if item is None and create_if_missing:
        InventoryItem.objects.get_or_create(warehouse=warehouse, material=material, defaults={"quantity": 0})
        item = InventoryItem.objects.select_for_update().get(warehouse=warehouse, material=material)
    return item


def ensure_sufficient_stock(item, warehouse, material, quantity):
    available = item.quantity if item else Decimal("0")
    if available < quantity:
        raise InsufficientStockError(
            f"{warehouse.name} omborida {material.name} yetarli emas "
            f"(mavjud: {available}, so'ralgan: {quantity})"
        )


def create_low_stock_notifications(item):
    threshold = item.min_quantity or Decimal("10")
    if item.quantity > threshold:
        return

    title = "Kam zaxira ogohlantirishi"
    message = f"{item.material.name} materiali {item.warehouse.name} omborida minimal chegaraga tushdi."
    notify_branch_roles(item.warehouse.branch, {"warehouse", "branch_manager", "admin"}, title, message, "warning")


def scoped_audit_logs(user):
    queryset = AuditLog.objects.select_related("user").order_by("-created_at")
    if is_admin(user):
        return queryset
    if not user.branch_id:
        # Filialsiz foydalanuvchiga faqat o'z izlari ko'rinadi.
        return queryset.filter(user=user)

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
    permission_classes = (permissions.AllowAny,)


class CustomTokenRefreshView(APIView):
    """
    JWT refresh.

    Ishni simplejwt'ning `TokenRefreshSerializer`iga topshiramiz — faqat shunda
    SIMPLE_JWT dagi ROTATE_REFRESH_TOKENS va BLACKLIST_AFTER_ROTATION haqiqatan
    ishlaydi (qo'lda yig'ilgan javob ularni jimgina chetlab o'tardi va bitta
    refresh token 7 kun davomida amal qilaverardi). O'zimizga faqat xato
    matnlari qoladi.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if not request.data.get('refresh'):
            return Response(
                {'error': 'refresh token topilmadi'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            return Response(
                {'error': "Refresh token yaroqsiz yoki muddati tugagan"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout - refresh tokenni blacklist qilish."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'refresh token topilmadi'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            # Token allaqachon blacklistda yoki muddati tugagan — maqsadga
            # baribir erishilgan, shuning uchun buni xato deb hisoblamaymiz.
            # (Ilgari bu yerda `str(e)` qaytarilib, ichki xabar tashqariga
            # chiqib ketardi.)
            pass

        return Response({'message': 'Muvaffaqiyatli chiqildi'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Parolni o'zgartirish."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': "old_password va new_password majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.check_password(old_password):
            return Response({'error': "Eski parol noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({'new_password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])

        create_audit_log(
            request,
            "password_changed",
            "User",
            user.id,
            {"email": user.email},
        )
        return Response({'message': "Parol muvaffaqiyatli o'zgartirildi"}, status=status.HTTP_200_OK)


class UserRegisterView(generics.CreateAPIView):
    """Ro'yxatdan o'tish."""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)
    
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


class UserListView(generics.ListCreateAPIView):
    """Foydalanuvchilar ro'yxati va yaratish (faqat admin)."""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.select_related("branch").order_by("-created_at")

    def get_serializer_class(self):
        return UserCreateSerializer if self.request.method == "POST" else UserSerializer

    def list(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Bu bo'limga faqat admin kira oladi"}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchi yaratish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        create_audit_log(request, "user_created", "User", user.id, {"email": user.email, "roles": user.roles})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Foydalanuvchi tafsilotlari, tahrirlash va o'chirish (faqat admin)."""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.select_related("branch")

    def get_serializer_class(self):
        return UserUpdateSerializer if self.request.method in ("PUT", "PATCH") else UserSerializer

    def retrieve(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Bu bo'limga faqat admin kira oladi"}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchini tahrirlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        create_audit_log(request, "user_updated", "User", user.id, {"email": user.email, "roles": user.roles})
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchini o'chirish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        instance = self.get_object()
        if instance.id == request.user.id:
            return Response({"error": "O'zingizni o'chira olmaysiz"}, status=status.HTTP_400_BAD_REQUEST)

        create_audit_log(request, "user_deleted", "User", instance.id, {"email": instance.email})
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                Q(quantity__lte=F("min_quantity")) | Q(min_quantity=0, quantity__lte=10)
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
        low_stock_items = inventory.filter(Q(quantity__lte=F("min_quantity")) | Q(min_quantity=0, quantity__lte=10))

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
        document = save_with_unique_number(
            lambda: serializer.save(
                created_by=self.request.user,
                branch=branch,
                doc_number=build_document_number(serializer.validated_data["doc_type"]),
            )
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
            # Xaridlar bo'limi so'rovni boshidanoq kuzatadi — arxitektura
            # javobini kutmasdan filial rahbariga tuzatish aytishi uchun.
            {"architecture", "procurement", "branch_manager", "admin"},
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
            {
                "architecture",
                "ceo",
                "procurement",
                "anticorruption",
                "accountant",
                "warehouse",
                "branch_manager",
                "admin",
            },
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

    def _ensure_can_manage(self, document):
        """
        Hujjatni faqat muallifi yoki hujjat oqimiga mas'ul rollar
        o'zgartira/o'chira oladi. Ilgari o'z filialidagi istalgan xodim
        begona hujjatni o'chirib yubora olardi.
        """
        user = self.request.user
        if document.created_by_id == user.id or has_any_role(user, DOCUMENT_MANAGE_ROLES):
            return
        raise exceptions.PermissionDenied("Bu hujjatni o'zgartirish uchun sizda ruxsat yo'q")

    def update(self, request, *args, **kwargs):
        self._ensure_can_manage(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        self._ensure_can_manage(document)

        create_audit_log(
            request,
            "document_deleted",
            "Document",
            document.id,
            {"doc_number": document.doc_number, "branch_id": document.branch_id},
        )
        return super().destroy(request, *args, **kwargs)


# --- Purchase Order Views ---
def _purchase_order_write_allowed(user):
    return is_admin(user) or bool(set(user.roles or []).intersection(PURCHASE_ORDER_ROLES))


class PurchaseOrderListView(generics.ListCreateAPIView):
    """Xarid buyurtmalari ro'yxati va yaratish."""
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        return PurchaseOrderCreateSerializer if self.request.method == "POST" else PurchaseOrderSerializer

    def get_queryset(self):
        return branch_scope(
            PurchaseOrder.objects.select_related("document", "document__branch", "supplier")
            .prefetch_related("items__material"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def create(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasi yaratish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            purchase_order = serializer.save()

        create_audit_log(
            request,
            "purchase_order_created",
            "PurchaseOrder",
            purchase_order.id,
            {"document_id": purchase_order.document_id, "supplier_id": purchase_order.supplier_id},
        )
        return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Xarid buyurtmasi tafsilotlari, tahrirlash va o'chirish."""
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        return PurchaseOrderUpdateSerializer if self.request.method in ("PUT", "PATCH") else PurchaseOrderSerializer

    def get_queryset(self):
        return branch_scope(
            PurchaseOrder.objects.select_related("document", "document__branch", "supplier")
            .prefetch_related("items__material"),
            self.request.user,
            "document__branch",
        )

    def update(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasini tahrirlash uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            purchase_order = serializer.save()

        create_audit_log(
            request,
            "purchase_order_updated",
            "PurchaseOrder",
            purchase_order.id,
            {"supplier_id": purchase_order.supplier_id},
        )
        return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasini o'chirish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()
        # `doc_number` ni ham yozamiz: buyurtma o'chgach jurnal uni bazadan topa
        # olmaydi va nomni shu yerdan oladi (serializers.AUDIT_DETAIL_LABEL_KEYS).
        create_audit_log(
            request,
            "purchase_order_deleted",
            "PurchaseOrder",
            instance.id,
            {"document_id": instance.document_id, "doc_number": instance.document.doc_number},
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Material Views ---
class MaterialListView(generics.ListCreateAPIView):
    """Materiallar ro'yxati va yaratish."""
    serializer_class = MaterialSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Material.objects.all()


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Material tahrirlash va o'chirish."""
    serializer_class = MaterialSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Material.objects.all()


# --- Warehouse Views ---
class WarehouseListView(generics.ListCreateAPIView):
    """Omborxonalar ro'yxati va yaratish."""
    serializer_class = WarehouseSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Warehouse.objects.select_related("branch").all()

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user)


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Omborxona tahrirlash va o'chirish."""
    serializer_class = WarehouseSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Warehouse.objects.select_related("branch").all()

    def get_queryset(self):
        # Ro'yxat filial bo'yicha filtrlanadi — tafsilot ham shunday bo'lishi
        # kerak, aks holda id ni taxmin qilib begona filial omborini o'qish,
        # tahrirlash va o'chirish mumkin edi.
        return branch_scope(super().get_queryset(), self.request.user)


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

    def create(self, request, *args, **kwargs):
        # Yangi zaxira yozuvi ham StockMovement (IN) tug'diradi — shuning uchun
        # ombor harakati bilan bir xil rol talab qilinadi.
        if not can_manage_stock(request.user):
            return Response(
                {"error": "Zaxira yozuvini yaratish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

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
        if not can_manage_stock(request.user):
            return Response(
                {"error": "Zaxirani o'zgartirish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

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


class StockMovementListView(generics.ListCreateAPIView):
    """Materiallar harakati tarixi va yangi harakat yaratish."""

    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StockMovementCreateSerializer
        return StockMovementSerializer

    def get_queryset(self):
        queryset = branch_scope(
            StockMovement.objects.select_related(
                "warehouse", "warehouse__branch", "target_warehouse", "material", "performed_by"
            ),
            self.request.user,
            "warehouse__branch",
        ).order_by("-performed_at")
        queryset = filter_by_query_params(
            queryset,
            self.request,
            {"material": "material_id", "movement_type": "movement_type"},
        )
        # Ombor bo'yicha filtr TRANSFER ni ikkala tomonda ham ko'rsatadi
        warehouse = self.request.query_params.get("warehouse")
        if warehouse:
            queryset = queryset.filter(Q(warehouse_id=warehouse) | Q(target_warehouse_id=warehouse))
        return queryset

    def create(self, request, *args, **kwargs):
        if not can_manage_stock(request.user):
            return Response(
                {"error": "Ombor harakatini yaratish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StockMovementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        warehouse = data["warehouse"]
        target_warehouse = data.get("target_warehouse")
        material = data["material"]
        movement_type = data["movement_type"]
        quantity = data["quantity"]

        # Admin uchun cheklov yo'q; qolganlar uchun manba ham, maqsad ham o'z filialida bo'lishi shart
        if not is_admin(request.user):
            for candidate in (warehouse, target_warehouse):
                if candidate and candidate.branch_id != request.user.branch_id:
                    return Response(
                        {"error": "Siz faqat o'z filialingiz omborlari bilan ishlashingiz mumkin"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        try:
            with transaction.atomic():
                if movement_type == "IN":
                    item = lock_inventory_item(warehouse, material, create_if_missing=True)
                    item.quantity += quantity
                    item.save(update_fields=["quantity", "updated_at"])
                    touched_items = [item]
                elif movement_type == "OUT":
                    item = lock_inventory_item(warehouse, material)
                    ensure_sufficient_stock(item, warehouse, material, quantity)
                    item.quantity -= quantity
                    item.save(update_fields=["quantity", "updated_at"])
                    touched_items = [item]
                else:
                    # Deadlock oldini olish uchun omborlarni id bo'yicha tartib bilan qulflaymiz
                    first, second = sorted([warehouse, target_warehouse], key=lambda w: w.id)
                    locked = {
                        first.id: lock_inventory_item(first, material, create_if_missing=first == target_warehouse),
                        second.id: lock_inventory_item(second, material, create_if_missing=second == target_warehouse),
                    }
                    source_item = locked[warehouse.id]
                    target_item = locked[target_warehouse.id]
                    ensure_sufficient_stock(source_item, warehouse, material, quantity)

                    source_item.quantity -= quantity
                    source_item.save(update_fields=["quantity", "updated_at"])
                    target_item.quantity += quantity
                    target_item.save(update_fields=["quantity", "updated_at"])
                    touched_items = [source_item, target_item]

                movement = serializer.save(performed_by=request.user)
        except InsufficientStockError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        for item in touched_items:
            create_low_stock_notifications(item)

        create_audit_log(
            request,
            "stock_movement_created",
            "StockMovement",
            movement.id,
            {
                "movement_type": movement.movement_type,
                "warehouse_id": movement.warehouse_id,
                "target_warehouse_id": movement.target_warehouse_id,
                "material_id": movement.material_id,
                "quantity": str(movement.quantity),
                "branch_id": movement.warehouse.branch_id,
            },
        )
        return Response(
            StockMovementSerializer(movement).data,
            status=status.HTTP_201_CREATED,
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
    permission_classes = (permissions.IsAuthenticated, SiteWrite)
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
    permission_classes = (permissions.IsAuthenticated, SiteWrite)
    queryset = ConstructionSite.objects.select_related("branch", "prorab")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user)


# --- Branch Views ---
class BranchListView(generics.ListCreateAPIView):
    """Filiallar ro'yxati."""
    serializer_class = BranchSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Branch.objects.all().order_by("name")


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Filial tahrirlash va o'chirish."""
    serializer_class = BranchSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Branch.objects.all()


# --- Supplier Views ---
class SupplierListView(generics.ListCreateAPIView):
    """Etkazib beruvchilar ro'yxati."""
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticated, SupplierWrite)
    queryset = Supplier.objects.all().order_by("name")


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Etkazib beruvchi tahrirlash va o'chirish."""
    serializer_class = SupplierSerializer
    permission_classes = (permissions.IsAuthenticated, SupplierWrite)
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
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
    queryset = Address.objects.all()


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manzil tahrirlash va o'chirish."""
    serializer_class = AddressSerializer
    permission_classes = (permissions.IsAuthenticated, AdminOnlyWrite)
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
        # Fayllar ro'yxati filial bo'yicha filtrlanadi; yuklash ham shunday
        # cheklanishi kerak, aks holda begona filial hujjatiga fayl ilib
        # qo'yish mumkin edi.
        document = branch_scope(
            Document.objects.select_related("branch"), request.user
        ).filter(id=doc_pk).first()
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
def _contract_write_allowed(user):
    return is_admin(user) or bool(set(user.roles or []).intersection(CONTRACT_ROLES))


class ContractListView(generics.ListCreateAPIView):
    """Shartnomalar ro'yxati va yaratish."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer

    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def create(self, request, *args, **kwargs):
        if not _contract_write_allowed(request.user):
            return Response(
                {"error": "Shartnoma yaratish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()

        create_audit_log(
            request,
            "contract_created",
            "Contract",
            contract.id,
            {"document_id": contract.document_id, "supplier_id": contract.supplier_id},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContractDetailView(generics.RetrieveUpdateAPIView):
    """Shartnoma tafsilotlari va tahrirlash."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer

    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def update(self, request, *args, **kwargs):
        if not _contract_write_allowed(request.user):
            return Response(
                {"error": "Shartnomani tahrirlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()

        create_audit_log(request, "contract_updated", "Contract", contract.id, {"supplier_id": contract.supplier_id})
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Invoice Views ---
class InvoiceListView(generics.ListCreateAPIView):
    """Hisob-fakturalar ro'yxati."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated, InvoiceWrite)
    queryset = Invoice.objects.select_related("document", "contract", "document__branch").order_by("-invoice_date")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user, "document__branch")


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    """Hisob-faktura tafsilotlari."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated, InvoiceWrite)
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
    permission_classes = (permissions.IsAuthenticated, PaymentWrite)
    
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
        prefix = f"PR-{timezone.localdate().strftime('%Y%m%d')}-"
        save_with_unique_number(
            lambda: serializer.save(
                created_by=self.request.user,
                request_number=(
                    f"{prefix}"
                    f"{next_sequence_number(ProductionRequest.objects, 'request_number', prefix):04d}"
                ),
            )
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

        # Admin uchun ilgari shu yerda `return qs` bor edi va status/priority/
        # category filtrlari jimgina e'tiborsiz qolardi — ro'yxat filtrlanmagan
        # holda qaytar edi. Endi ko'rish doirasi va filtr ajratilgan.
        if not is_admin(user):
            qs = qs.filter(branch=user.branch) if user.branch_id else qs.filter(created_by=user)

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
