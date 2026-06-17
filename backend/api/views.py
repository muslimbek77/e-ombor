from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from django.db.models import Count, Q, Sum
from .models import (
    User, Document, PurchaseOrder, PurchaseOrderItem, Supplier,
    Material, InventoryItem, Warehouse, ConstructionSite, Branch,
    Notification, AuditLog, Address, DocumentFile, Contract, Invoice, Payment,
    ProductionRequest, Ticket
)
from .serializers import (
    UserSerializer, UserRegisterSerializer, CustomTokenObtainPairSerializer,
    DocumentSerializer, SupplierSerializer, MaterialSerializer,
    InventoryItemSerializer, WarehouseSerializer, ConstructionSiteSerializer,
    BranchSerializer, NotificationSerializer, DashboardStatsSerializer,
    AddressSerializer, DocumentFileSerializer, ContractSerializer,
    InvoiceSerializer, PaymentSerializer, ProductionRequestSerializer,
    TicketSerializer
)


class CustomTokenObtainPairView(CustomTokenObtainPairSerializer, TokenObtainPairView):
    """JWT Token olish (login)."""
    pass


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
        
        # General stats
        total_documents = Document.objects.count()
        pending_approvals = Document.objects.filter(
            status__in=['architecture', 'ceo']
        ).count()
        total_materials = Material.objects.count()
        total_warehouses = Warehouse.objects.count()
        total_sites = ConstructionSite.objects.count()
        low_stock_items = InventoryItem.objects.filter(
            Q(quantity__lte=Q(min_quantity)) | Q(min_quantity=0, quantity__lt=10)
        ).count()
        
        # Recent documents
        recent_docs = Document.objects.select_related('created_by').order_by('-created_at')[:5]
        
        # User notifications
        notifications = Notification.objects.filter(
            user=user, is_read=False
        ).order_by('-created_at')[:10]
        
        stats = {
            'total_documents': total_documents,
            'pending_approvals': pending_approvals,
            'total_materials': total_materials,
            'total_warehouses': total_warehouses,
            'total_sites': total_sites,
            'low_stock_items': low_stock_items,
            'recent_documents': DocumentSerializer(recent_docs, many=True).data,
            'notifications': NotificationSerializer(notifications, many=True).data,
        }
        
        return Response(stats, status=status.HTTP_200_OK)


# --- Document Views ---
class DocumentListCreateView(generics.ListCreateAPIView):
    """Hujjatlar ro'yxati va yaratish."""
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        user = self.request.user
        queryset = Document.objects.select_related(
            'created_by', 'site', 'branch'
        ).order_by('-created_at')
        
        # Admin hammasini ko'radi
        if user.is_staff or 'admin' in user.roles:
            return queryset
        
        # Boshqa foydalanuvchilar faqat o'z filialini ko'radi
        if user.branch:
            queryset = queryset.filter(branch=user.branch)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            branch=self.request.user.branch
        )


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Hujjat tahrirlash va o'chirish."""
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Document.objects.select_related(
            'created_by', 'site', 'branch'
        ).order_by('-created_at')


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
                'items': PurchaseOrderItemSerializer(order.items, many=True).data,
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
    queryset = Warehouse.objects.all()


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Omborxona tahrirlash va o'chirish."""
    serializer_class = WarehouseSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Warehouse.objects.all()


# --- Inventory Views ---
class InventoryListView(generics.ListAPIView):
    """Ombor zaxiralari ro'yxati."""
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return InventoryItem.objects.select_related(
            'warehouse', 'material'
        ).order_by('material__name')


class InventoryUpdateView(generics.UpdateAPIView):
    """Ombor zaxirasini yangilash."""
    serializer_class = InventoryItemSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return InventoryItem.objects.all()


# --- Construction Site Views ---
class ConstructionSiteListView(generics.ListCreateAPIView):
    """Qurilish obyektlari ro'yxati va yaratish."""
    serializer_class = ConstructionSiteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = ConstructionSite.objects.all()
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.branch:
            qs = qs.filter(branch=user.branch)
        return qs


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
    queryset = Branch.objects.all()


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
    queryset = Supplier.objects.all()


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
        return Notification.objects.filter(user=self.request.user)


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
        return DocumentFile.objects.filter(document_id=doc_id).order_by('-created_at')


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
        
        DocumentFile.objects.create(
            document=document,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            uploaded_by=request.user
        )
        
        return Response({'message': 'Fayl muvaffaqiyatli yuklandi'}, status=status.HTTP_201_CREATED)


# --- Contract Views ---
class ContractListView(generics.ListAPIView):
    """Shartnomalar ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer
    
    def get_queryset(self):
        return Contract.objects.select_related('document', 'supplier').order_by('-document__created_at')


class ContractDetailView(generics.RetrieveAPIView):
    """Shartnoma tafsilotlari."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ContractSerializer
    
    def get_queryset(self):
        return Contract.objects.select_related('document', 'supplier').order_by('-document__created_at')


# --- Invoice Views ---
class InvoiceListView(generics.ListCreateAPIView):
    """Hisob-fakturalar ro'yxati."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Invoice.objects.select_related('document', 'contract').order_by('-invoice_date')


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    """Hisob-faktura tafsilotlari."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Invoice.objects.select_related('document', 'contract').order_by('-invoice_date')


# --- Payment Views ---
class PaymentListView(generics.ListAPIView):
    """To'lovlar ro'yxati."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return Payment.objects.select_related('invoice', 'performed_by').order_by('-payment_date')


class PaymentCreateView(generics.CreateAPIView):
    """To'lov yaratish."""
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def perform_create(self, serializer):
        invoice_id = self.kwargs.get('invoice_pk')
        invoice = Invoice.objects.filter(id=invoice_id).first()
        if not invoice:
            raise serializers.ValidationError("Hisob-faktura topilmadi")
        
        payment = serializer.save(performed_by=self.request.user)
        
        # Update invoice paid amount
        invoice.paid_amount += payment.amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = 'paid'
        elif invoice.paid_amount > 0:
            invoice.payment_status = 'partial'
        invoice.save()


# --- Production Request Views ---
class ProductionRequestListView(generics.ListCreateAPIView):
    """Ishlab chiqarish zayavkalari ro'yxati."""
    serializer_class = ProductionRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return ProductionRequest.objects.select_related('site', 'created_by').order_by('-created_at')
    
    def perform_create(self, serializer):
        import datetime
        today = datetime.datetime.now().strftime('%Y%m%d')
        count = ProductionRequest.objects.filter(
            created_at__date=datetime.date.today()
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
        return ProductionRequest.objects.select_related('site', 'created_by').order_by('-created_at')


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
            return qs.filter(branch=user.branch)
        
        return qs.filter(created_by=user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


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
