from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Document, PurchaseOrder, PurchaseOrderItem, Supplier,
    Material, InventoryItem, Warehouse, ConstructionSite, Branch,
    Notification, Address, DocumentFile, Contract, Invoice, Payment,
    ProductionRequest, Ticket
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchi ma'lumotlari serializeri."""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email',
            'phone', 'stir_inn', 'roles', 'branch',
            'is_active', 'is_staff', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Ro'yxatdan o'tish serializeri."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'stir_inn', 'roles']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token olish serializeri."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['roles'] = user.roles
        token['full_name'] = user.full_name
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class DocumentSerializer(serializers.ModelSerializer):
    """Hujjatlar serializeri."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'doc_number', 'doc_type', 'status', 'title', 'description',
            'created_by', 'created_by_name', 'site', 'branch',
            'total_amount', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['doc_number', 'created_at', 'updated_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Xarid buyurtma qatorlari serializeri."""
    material_name = serializers.CharField(source='material.name', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'purchase_order', 'material', 'material_name', 'quantity', 'unit_price', 'total_price']


class SupplierSerializer(serializers.ModelSerializer):
    """Etkazib beruvchilar serializeri."""
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'code', 'contact_person', 'phone', 'email', 'address', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class MaterialSerializer(serializers.ModelSerializer):
    """Materiallar serializeri."""
    class Meta:
        model = Material
        fields = ['id', 'name', 'code', 'unit', 'category', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class InventoryItemSerializer(serializers.ModelSerializer):
    """Ombor zaxirasi serializeri."""
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_code = serializers.CharField(source='material.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = ['id', 'warehouse', 'warehouse_name', 'material', 'material_name', 'material_code', 
                  'quantity', 'min_quantity', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class WarehouseSerializer(serializers.ModelSerializer):
    """Omborxonalar serializeri."""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'code', 'branch', 'branch_name', 'address', 'min_stock_alert', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConstructionSiteSerializer(serializers.ModelSerializer):
    """Qurilish obyektlari serializeri."""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    prorab_name = serializers.CharField(source='prorab.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ConstructionSite
        fields = [
            'id', 'name', 'code', 'branch', 'branch_name', 'address',
            'status', 'status_display', 'budget', 'prorab', 'prorab_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BranchSerializer(serializers.ModelSerializer):
    """Filiallar serializeri."""
    class Meta:
        model = Branch
        fields = ['id', 'name', 'code', 'address', 'phone', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Bildirishnomalar serializeri."""
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'notification_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistikalari serializeri."""
    total_documents = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    total_materials = serializers.IntegerField()
    total_warehouses = serializers.IntegerField()
    total_sites = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
    recent_documents = DocumentSerializer(many=True, read_only=True)
    notifications = NotificationSerializer(many=True, read_only=True)


class AddressSerializer(serializers.ModelSerializer):
    """Manzillar serializeri."""
    class Meta:
        model = Address
        fields = ['id', 'city', 'district', 'street', 'building']


class DocumentFileSerializer(serializers.ModelSerializer):
    """Hujjat fayllari serializeri."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    
    class Meta:
        model = DocumentFile
        fields = ['id', 'document', 'file', 'original_filename', 'file_size', 
                  'uploaded_by', 'uploaded_by_name', 'created_at']
        read_only_fields = ['id', 'created_at', 'uploaded_by_name']


class ContractSerializer(serializers.ModelSerializer):
    """Shartnomalar serializeri."""
    document_doc_number = serializers.CharField(source='document.doc_number', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Contract
        fields = ['id', 'document', 'document_doc_number', 'supplier', 'supplier_name',
                  'contract_number', 'signed_date', 'start_date', 'end_date',
                  'total_amount', 'description']


class InvoiceSerializer(serializers.ModelSerializer):
    """Hisob-fakturalar serializeri."""
    document_doc_number = serializers.CharField(source='document.doc_number', read_only=True)
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = ['id', 'document', 'document_doc_number', 'contract', 'contract_number',
                  'invoice_number', 'invoice_date', 'due_date', 'total_amount', 
                  'paid_amount', 'remaining_amount', 'payment_status', 
                  'payment_status_display']


class PaymentSerializer(serializers.ModelSerializer):
    """To'lovlar serializeri."""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'invoice_number', 'amount', 'payment_date',
                  'payment_method', 'reference_number', 'performed_by', 
                  'performed_by_name', 'notes']
        read_only_fields = ['id', 'payment_date', 'performed_by_name']


class ProductionRequestSerializer(serializers.ModelSerializer):
    """Ishlab chiqarish zayavkalari serializeri."""
    site_name = serializers.CharField(source='site.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ProductionRequest
        fields = ['id', 'site', 'site_name', 'request_number', 'title', 'description',
                  'status', 'status_display', 'created_by', 'created_by_name', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'request_number', 'created_at', 'updated_at', 'created_by_name', 'status_display']


class TicketSerializer(serializers.ModelSerializer):
    """Murojaat tizimi serializeri."""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = ['id', 'title', 'description', 'category', 'category_display',
                  'priority', 'priority_display', 'status', 'status_display',
                  'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name',
                  'branch', 'branch_name', 'site', 'site_name',
                  'response', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_name', 
                          'assigned_to_name', 'branch_name', 'site_name',
                          'priority_display', 'status_display', 'category_display']
