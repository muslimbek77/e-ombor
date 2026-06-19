from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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
    PurchaseOrderItem,
    StockMovement,
    Supplier,
    Ticket,
    Warehouse,
)

User = get_user_model()
ARCHIVE_VISIBLE_ROLES = {"admin", "procurement", "branch_manager"}
SERIALIZER_WORKFLOW_RULES = {
    "created": {"submit": {"roles": {"prorab", "procurement", "admin"}}},
    "architecture": {
        "approve": {"roles": {"architecture", "admin"}},
        "reject": {"roles": {"architecture", "admin"}},
    },
    "ceo": {
        "approve": {"roles": {"ceo", "admin"}},
        "reject": {"roles": {"ceo", "admin"}},
    },
    "approved": {
        "advance": {"roles": {"procurement", "admin"}},
        "reject": {"roles": {"procurement", "admin"}},
    },
    "contract": {
        "advance": {"roles": {"procurement", "accountant", "admin"}},
        "reject": {"roles": {"procurement", "accountant", "admin"}},
    },
    "payment": {
        "advance": {"roles": {"accountant", "admin"}},
        "reject": {"roles": {"accountant", "admin"}},
    },
    "delivering": {"advance": {"roles": {"warehouse", "admin"}}},
    "received": {"close": {"roles": {"warehouse", "prorab", "admin"}}},
    "rejected": {"reopen": {"roles": {"admin", "procurement", "prorab"}}},
}


class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchi ma'lumotlari serializeri."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "stir_inn",
            "roles",
            "branch",
            "branch_name",
            "is_active",
            "is_staff",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "last_login", "branch_name"]


class UserRegisterSerializer(serializers.ModelSerializer):
    """Ro'yxatdan o'tish serializeri."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "stir_inn",
            "roles",
            "branch",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token olish serializeri."""

    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["roles"] = user.roles
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class DocumentApprovalSerializer(serializers.ModelSerializer):
    """Hujjat bo'yicha tasdiqlashlar tarixi."""

    approver_name = serializers.CharField(source="approver.full_name", read_only=True)

    class Meta:
        model = DocumentApproval
        fields = ["id", "action", "comment", "created_at", "approver", "approver_name"]
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    """Hujjatlar serializeri."""

    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    approvals = DocumentApprovalSerializer(many=True, read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    can_archive = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "doc_number",
            "doc_type",
            "status",
            "status_display",
            "title",
            "description",
            "created_by",
            "created_by_name",
            "site",
            "site_name",
            "branch",
            "branch_name",
            "total_amount",
            "notes",
            "is_archived",
            "archived_at",
            "created_at",
            "updated_at",
            "approvals",
            "allowed_actions",
            "can_archive",
        ]
        read_only_fields = [
            "doc_number",
            "created_at",
            "updated_at",
            "created_by_name",
            "status_display",
            "site_name",
            "branch_name",
            "approvals",
            "allowed_actions",
            "archived_at",
            "can_archive",
        ]

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
            return []

        user = request.user
        user_roles = set(user.roles or [])
        actions = SERIALIZER_WORKFLOW_RULES.get(obj.status, {})
        return [
            action
            for action, config in actions.items()
            if user.is_staff or bool(user_roles.intersection(config["roles"]))
        ]

    def get_can_archive(self, obj):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
            return False
        user = request.user
        return user.is_staff or bool(set(user.roles or []).intersection(ARCHIVE_VISIBLE_ROLES))


class DocumentWorkflowSerializer(serializers.Serializer):
    """Hujjat workflow amallari uchun serializer."""

    action = serializers.ChoiceField(
        choices=[
            "submit",
            "approve",
            "advance",
            "close",
            "reject",
            "reopen",
        ]
    )
    comment = serializers.CharField(required=False, allow_blank=True)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Xarid buyurtma qatorlari serializeri."""

    material_name = serializers.CharField(source="material.name", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "purchase_order", "material", "material_name", "quantity", "unit_price", "total_price"]


class SupplierSerializer(serializers.ModelSerializer):
    """Etkazib beruvchilar serializeri."""

    class Meta:
        model = Supplier
        fields = ["id", "name", "code", "contact_person", "phone", "email", "address", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class MaterialSerializer(serializers.ModelSerializer):
    """Materiallar serializeri."""

    class Meta:
        model = Material
        fields = ["id", "name", "code", "unit", "category", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class InventoryItemSerializer(serializers.ModelSerializer):
    """Ombor zaxirasi serializeri."""

    material_name = serializers.CharField(source="material.name", read_only=True)
    material_code = serializers.CharField(source="material.code", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    branch_name = serializers.CharField(source="warehouse.branch.name", read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "branch_name",
            "material",
            "material_name",
            "material_code",
            "quantity",
            "min_quantity",
            "updated_at",
            "is_low_stock",
        ]
        read_only_fields = ["id", "updated_at", "warehouse_name", "branch_name", "material_name", "material_code"]

    def get_is_low_stock(self, obj):
        threshold = obj.min_quantity or 10
        return obj.quantity <= threshold


class InventoryAdjustmentSerializer(serializers.Serializer):
    """Inventory miqdorini qo'lda tuzatish serializeri."""

    quantity_delta = serializers.DecimalField(max_digits=12, decimal_places=3, required=False, default=0)
    min_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class StockMovementSerializer(serializers.ModelSerializer):
    """Materiallar harakati serializeri."""

    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    material_name = serializers.CharField(source="material.name", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "material",
            "material_name",
            "movement_type",
            "movement_type_display",
            "quantity",
            "performed_by",
            "performed_by_name",
            "performed_at",
            "notes",
        ]
        read_only_fields = fields


class WarehouseSerializer(serializers.ModelSerializer):
    """Omborxonalar serializeri."""

    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Warehouse
        fields = ["id", "name", "code", "branch", "branch_name", "address", "min_stock_alert", "created_at"]
        read_only_fields = ["id", "created_at", "branch_name"]


class ConstructionSiteSerializer(serializers.ModelSerializer):
    """Qurilish obyektlari serializeri."""

    branch_name = serializers.CharField(source="branch.name", read_only=True)
    prorab_name = serializers.CharField(source="prorab.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ConstructionSite
        fields = [
            "id",
            "name",
            "code",
            "branch",
            "branch_name",
            "address",
            "status",
            "status_display",
            "budget",
            "prorab",
            "prorab_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "branch_name", "prorab_name", "status_display"]


class BranchSerializer(serializers.ModelSerializer):
    """Filiallar serializeri."""

    class Meta:
        model = Branch
        fields = ["id", "name", "code", "address", "phone", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    """Bildirishnomalar serializeri."""

    class Meta:
        model = Notification
        fields = ["id", "title", "message", "is_read", "notification_type", "created_at"]
        read_only_fields = ["id", "created_at"]


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
        fields = ["id", "city", "district", "street", "building"]


class DocumentFileSerializer(serializers.ModelSerializer):
    """Hujjat fayllari serializeri."""

    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = DocumentFile
        fields = ["id", "document", "file", "original_filename", "file_size", "uploaded_by", "uploaded_by_name", "created_at"]
        read_only_fields = ["id", "created_at", "uploaded_by_name"]


class ContractSerializer(serializers.ModelSerializer):
    """Shartnomalar serializeri."""

    document_doc_number = serializers.CharField(source="document.doc_number", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "document",
            "document_doc_number",
            "supplier",
            "supplier_name",
            "contract_number",
            "signed_date",
            "start_date",
            "end_date",
            "total_amount",
            "description",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """Hisob-fakturalar serializeri."""

    document_doc_number = serializers.CharField(source="document.doc_number", read_only=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "document",
            "document_doc_number",
            "contract",
            "contract_number",
            "invoice_number",
            "invoice_date",
            "due_date",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "payment_status",
            "payment_status_display",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """To'lovlar serializeri."""

    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "invoice",
            "invoice_number",
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "performed_by",
            "performed_by_name",
            "notes",
        ]
        read_only_fields = ["id", "payment_date", "performed_by_name", "invoice_number", "performed_by"]
        extra_kwargs = {"invoice": {"required": False}}


class ProductionRequestSerializer(serializers.ModelSerializer):
    """Ishlab chiqarish zayavkalari serializeri."""

    site_name = serializers.CharField(source="site.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProductionRequest
        fields = [
            "id",
            "site",
            "site_name",
            "request_number",
            "title",
            "description",
            "status",
            "status_display",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "request_number", "created_at", "updated_at", "created_by_name", "status_display"]


class TicketSerializer(serializers.ModelSerializer):
    """Murojaat tizimi serializeri."""

    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "category",
            "category_display",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "created_by",
            "created_by_name",
            "assigned_to",
            "assigned_to_name",
            "branch",
            "branch_name",
            "site",
            "site_name",
            "response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by_name",
            "assigned_to_name",
            "branch_name",
            "site_name",
            "priority_display",
            "status_display",
            "category_display",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializeri."""

    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "details",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
