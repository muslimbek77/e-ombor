from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email manzil zarur')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('roles', [])
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email as unique identifier."""
    
    ROLES = [
        ('admin', 'Admin (Tizim administratori)'),
        ('ceo', 'Boshqaruv raisi'),
        ('architecture', 'Arxitektura va qurilishni rejalashtirish'),
        ('procurement', 'Xaridlar boshqarmasi'),
        ('accountant', 'Buxgalter'),
        ('warehouse', 'Omborchi'),
        ('prorab', 'Prorab (Foreman)'),
        ('branch_manager', 'Filial rahbari'),
    ]
    
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    stir_inn = models.CharField(max_length=20, blank=True, help_text='STIR yoki INN')
    roles = models.JSONField(default=list, help_text='Foydalanuvchi rollari')
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({', '.join(self.roles) if self.roles else 'No roles'})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Branch(models.Model):
    """Filiallar modeli."""
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'branches'
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ConstructionSite(models.Model):
    """Qurilish obyektlari."""
    
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('paused', 'To\'xtatilgan'),
        ('completed', 'Tugallangan'),
    ]
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sites')
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prorab = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sites'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'construction_sites'
        verbose_name = 'Qurilish obyekti'
        verbose_name_plural = 'Qurilish obyektlari'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(models.Model):
    """Omborxonalar."""
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    address = models.TextField(blank=True)
    min_stock_alert = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'warehouses'
        verbose_name = 'Omborxona'
        verbose_name_plural = 'Omborxonalar'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Material(models.Model):
    """Material/Mahsulot katalogi."""
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=50, default=' dona')
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'materials'
        verbose_name = 'Material'
        verbose_name_plural = 'Materiallar'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class InventoryItem(models.Model):
    """Ombordagi material zaxirasi."""
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    min_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0, help_text='Minimal zaxira')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_items'
        unique_together = ('warehouse', 'material')
    
    def __str__(self):
        return f"{self.warehouse.code} - {self.material.code}: {self.quantity}"


class StockMovement(models.Model):
    """Materiallar harakati (kirim/chiqim)."""
    
    MOVEMENT_TYPES = [
        ('IN', 'Kirim'),
        ('OUT', 'Chiqim'),
        ('TRANSFER', 'Ko\'chirish'),
    ]
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='movements')
    performed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.material.name} ({self.quantity})"


class Document(models.Model):
    """Hujjatlar (zayavka, shartnoma, invoice va h.k.)."""
    
    DOC_TYPES = [
        ('purchase_request', 'Xarid so\'rovi'),
        ('contract', 'Shartnoma'),
        ('invoice', 'Invoice'),
    ]
    
    STATUSES = [
        ('created', 'YARATILDI'),
        ('architecture', 'ARXITEKTURADA'),
        ('ceo', 'RAISDA'),
        ('approved', 'TASDIQLANDI'),
        ('contract', 'SHARTNOMADA'),
        ('payment', 'TO\'LOVDA'),
        ('delivering', 'YETKAZILMOQDA'),
        ('received', 'QABUL QILINDI'),
        ('closed', 'YOPILDI'),
        ('rejected', 'RAD ETILDI'),
    ]
    
    doc_number = models.CharField(max_length=50, unique=True)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES)
    status = models.CharField(max_length=20, choices=STATUSES, default='created')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_documents')
    site = models.ForeignKey(ConstructionSite, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, related_name='documents')
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.doc_number} - {self.title}"


class DocumentApproval(models.Model):
    """Hujjat tasdiqlash tarixi."""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approvals')
    action = models.CharField(max_length=20)  # approved, rejected
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_approvals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.doc_number} - {self.action}"


class PurchaseOrder(models.Model):
    """Xarid buyurtmalari."""
    
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='purchase_order')
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'purchase_orders'
    
    def __str__(self):
        return f"PO - {self.document.doc_number}"


class PurchaseOrderItem(models.Model):
    """Xarid buyurtma qatorlari."""
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'purchase_order_items'
    
    def __str__(self):
        return f"POI - {self.material.name} x {self.quantity}"


class Supplier(models.Model):
    """Etkazib beruvchilar."""
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'suppliers'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Notification(models.Model):
    """Bildirishnomalar."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class AuditLog(models.Model):
    """Audit log - barcha muhim amallar tarixi."""
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"
