from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
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

from .workflow import allowed_actions_for

User = get_user_model()
ARCHIVE_VISIBLE_ROLES = {"admin", "procurement", "branch_manager"}


class UserSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi ma'lumotlari serializeri.

    `UserProfileView` shu serializer bilan profilni tahrirlaydi, shuning uchun
    imtiyoz beruvchi maydonlar (rol, filial, staff bayrog'i) bu yerda faqat
    o'qish uchun. Aks holda oddiy xodim `PATCH /auth/user/` orqali o'ziga
    `admin` rolini yozib qo'ya olardi. Adminning o'zi ularni
    `UserCreateSerializer` / `UserUpdateSerializer` orqali o'zgartiradi.
    """

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
        read_only_fields = [
            "id",
            "email",
            "roles",
            "branch",
            "branch_name",
            "is_active",
            "is_staff",
            "last_login",
            "created_at",
            "updated_at",
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Ro'yxatdan o'tish serializeri.

    `roles` va `branch` bu yerda ataylab yo'q: register endpointi `AllowAny`,
    ya'ni maydonlar ochiq bo'lsa istalgan odam o'ziga `["admin"]` rolini yoki
    begona filialni biriktirib yubora olardi. Yangi hisob rolsiz va filialsiz
    tug'iladi — ikkalasini ham keyin admin beradi.
    """

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
        return allowed_actions_for(obj.status, user.roles, is_staff=user.is_staff)

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


class UserCreateSerializer(serializers.ModelSerializer):
    """Admin panelidan yangi foydalanuvchi yaratish."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "email", "password", "first_name", "last_name", "phone", "stir_inn",
            "roles", "branch", "is_active", "is_staff",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Admin panelidan foydalanuvchini tahrirlash. Parol faqat berilgan bo'lsa o'zgaradi."""

    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "phone", "stir_inn",
            "roles", "branch", "is_active", "is_staff", "password",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Xarid buyurtma qatorlari serializeri."""

    material_name = serializers.CharField(source="material.name", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ["id", "purchase_order", "material", "material_name", "quantity", "unit_price", "total_price"]


class PurchaseOrderItemInputSerializer(serializers.ModelSerializer):
    """Xarid buyurtmasini yaratish/tahrirlashda nested qator kiritish uchun."""

    class Meta:
        model = PurchaseOrderItem
        fields = ["material", "quantity", "unit_price", "total_price"]
        extra_kwargs = {"total_price": {"required": False}}

    def validate(self, attrs):
        if not attrs.get("total_price"):
            attrs["total_price"] = attrs["quantity"] * attrs["unit_price"]
        return attrs


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Xarid buyurtmasi - o'qish uchun (hujjat va qatorlar bilan)."""

    doc_number = serializers.CharField(source="document.doc_number", read_only=True)
    title = serializers.CharField(source="document.title", read_only=True)
    doc_status = serializers.CharField(source="document.status", read_only=True)
    total_amount = serializers.DecimalField(
        source="document.total_amount", max_digits=18, decimal_places=2, read_only=True
    )
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(source="document.created_at", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "document",
            "doc_number",
            "title",
            "doc_status",
            "total_amount",
            "supplier",
            "supplier_name",
            "items",
            "created_at",
        ]
        read_only_fields = [
            "id", "doc_number", "title", "doc_status", "total_amount", "supplier_name", "items", "created_at",
        ]


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    """Yangi xarid buyurtmasi yaratish (mavjud Document asosida, qatorlar bilan birga)."""

    items = PurchaseOrderItemInputSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ["document", "supplier", "items"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=purchase_order, **item_data)
        return purchase_order


class PurchaseOrderUpdateSerializer(serializers.ModelSerializer):
    """Xarid buyurtmasini tahrirlash: yetkazib beruvchi va (ixtiyoriy) qatorlarni almashtirish.

    ``document`` bu yerda qasddan kiritilmagan - buyurtma qaysi hujjatga
    tegishli ekanligi yaratilgandan keyin o'zgarmasligi kerak.
    """

    items = PurchaseOrderItemInputSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "items"]

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        instance.supplier = validated_data.get("supplier", instance.supplier)
        instance.save(update_fields=["supplier"])
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(purchase_order=instance, **item_data)
        return instance


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
    target_warehouse_name = serializers.CharField(source="target_warehouse.name", read_only=True)
    material_name = serializers.CharField(source="material.name", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "target_warehouse",
            "target_warehouse_name",
            "material",
            "material_name",
            "movement_type",
            "movement_type_display",
            "quantity",
            "reference_doc",
            "performed_by",
            "performed_by_name",
            "performed_at",
            "notes",
        ]
        read_only_fields = fields


class StockMovementCreateSerializer(serializers.ModelSerializer):
    """Yangi materiallar harakatini yaratish serializeri."""

    class Meta:
        model = StockMovement
        fields = [
            "warehouse",
            "target_warehouse",
            "material",
            "movement_type",
            "quantity",
            "reference_doc",
            "notes",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Miqdor noldan katta bo'lishi kerak")
        return value

    def validate(self, attrs):
        movement_type = attrs.get("movement_type")
        warehouse = attrs.get("warehouse")
        target_warehouse = attrs.get("target_warehouse")

        if movement_type == "TRANSFER":
            if not target_warehouse:
                raise serializers.ValidationError(
                    {"target_warehouse": "TRANSFER uchun maqsad ombor ko'rsatilishi shart"}
                )
            if target_warehouse == warehouse:
                raise serializers.ValidationError(
                    {"target_warehouse": "Maqsad ombor manba ombordan farq qilishi kerak"}
                )
        elif target_warehouse:
            raise serializers.ValidationError(
                {"target_warehouse": "target_warehouse faqat TRANSFER uchun ishlatiladi"}
            )

        return attrs


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


# --- Audit log obyekt nomlari ---
# Jurnalda `model_name` + `object_id` saqlanadi, lekin foydalanuvchiga raqam emas,
# obyektning o'zi ko'rinishi kerak. Har bir model uchun: (model, select_related, nom).
AUDIT_LABEL_SOURCES = {
    "Document": (Document, (), lambda o: f"{o.doc_number} — {o.title}"),
    "DocumentFile": (DocumentFile, ("document",), lambda o: o.original_filename),
    "Contract": (Contract, ("document",), lambda o: o.contract_number or o.document.doc_number),
    "PurchaseOrder": (
        PurchaseOrder,
        ("document", "supplier"),
        lambda o: f"{o.document.doc_number} — {o.supplier.name}" if o.supplier else o.document.doc_number,
    ),
    "Payment": (Payment, ("invoice",), lambda o: f"{o.invoice.invoice_number} — {o.amount}"),
    "InventoryItem": (
        InventoryItem,
        ("material", "warehouse"),
        lambda o: f"{o.material.name} — {o.warehouse.name}",
    ),
    "StockMovement": (
        StockMovement,
        ("material", "warehouse"),
        lambda o: f"{o.material.name} — {o.warehouse.name}",
    ),
    "Ticket": (Ticket, (), lambda o: o.title),
    "User": (User, (), lambda o: o.full_name.strip() or o.email),
    # Quyidagilarni hozircha faqat `seed_demo_data` yozadi, lekin demo bazada ular ham
    # jurnalda ko'rinadi — id qolib ketmasin.
    "Supplier": (Supplier, (), lambda o: o.name),
    "ConstructionSite": (ConstructionSite, (), lambda o: o.name),
    "ProductionRequest": (
        ProductionRequest,
        (),
        lambda o: f"{o.request_number} — {o.title}",
    ),
}

# Obyekt o'chirilgan bo'lsa bazadan topilmaydi — nomni `details` ichidan qidiramiz.
AUDIT_DETAIL_LABEL_KEYS = ("email", "title", "name", "doc_number", "contract_number", "invoice_number")


def build_audit_object_labels(logs):
    """`(model_name, object_id)` → o'qiladigan nom. Har bir model uchun bitta so'rov."""
    wanted = {}
    for log in logs:
        if log.object_id is None or log.model_name not in AUDIT_LABEL_SOURCES:
            continue
        wanted.setdefault(log.model_name, set()).add(log.object_id)

    labels = {}
    for model_name, ids in wanted.items():
        model, related, to_label = AUDIT_LABEL_SOURCES[model_name]
        queryset = model.objects.filter(pk__in=ids)
        if related:
            queryset = queryset.select_related(*related)
        for obj in queryset:
            try:
                label = to_label(obj)
            except (AttributeError, ObjectDoesNotExist):
                continue
            if label:
                labels[(model_name, obj.pk)] = str(label).strip()

    return labels


def audit_detail_label(log):
    details = log.details if isinstance(log.details, dict) else None
    if not details:
        return None

    for key in AUDIT_DETAIL_LABEL_KEYS:
        value = details.get(key)
        if value:
            return str(value)

    return None


class AuditLogListSerializer(serializers.ListSerializer):
    """Sahifadagi barcha yozuvlar uchun nomlarni oldindan yig'adi (N+1 bo'lmasin)."""

    def to_representation(self, data):
        items = list(data)
        self.child.object_labels = build_audit_object_labels(items)
        return super().to_representation(items)


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializeri."""

    user_name = serializers.CharField(source="user.full_name", read_only=True)
    object_label = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        list_serializer_class = AuditLogListSerializer
        fields = [
            "id",
            "user",
            "user_name",
            "action",
            "model_name",
            "object_id",
            "object_label",
            "details",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields

    def get_object_label(self, obj):
        """Obyekt topilmasa (o'chirilgan yoki noma'lum model) `None` — UI id ko'rsatadi."""
        labels = getattr(self, "object_labels", None)
        if labels is None:
            labels = build_audit_object_labels([obj])

        return labels.get((obj.model_name, obj.object_id)) or audit_detail_label(obj)
