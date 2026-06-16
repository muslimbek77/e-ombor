from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Branch, ConstructionSite, Warehouse, Material,
    InventoryItem, StockMovement, Document, DocumentApproval,
    PurchaseOrder, PurchaseOrderItem, Supplier, Notification, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'is_staff', 'is_active', 'roles', 'branch']
    list_filter = ['is_staff', 'is_active', 'roles']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'stir_inn', 'branch')}),
        ('Roles', {'fields': ('roles',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password', 'password_confirm'),
        }),
    )
    
    readonly_fields = ['last_login', 'created_at', 'updated_at']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'phone', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active']


@admin.register(ConstructionSite)
class ConstructionSiteAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'branch', 'status', 'prorab']
    list_filter = ['status', 'branch']
    search_fields = ['name', 'code']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'branch']
    search_fields = ['name', 'code']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit']
    search_fields = ['name', 'code']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'material', 'quantity', 'min_quantity']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'material', 'movement_type', 'quantity', 'performed_by', 'performed_at']
    list_filter = ['movement_type']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['doc_number', 'doc_type', 'status', 'created_by', 'total_amount', 'created_at']
    list_filter = ['doc_type', 'status']
    search_fields = ['doc_number', 'title']


@admin.register(DocumentApproval)
class DocumentApprovalAdmin(admin.ModelAdmin):
    list_display = ['document', 'approver', 'action', 'created_at']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['document', 'supplier']


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'material', 'quantity', 'unit_price', 'total_price']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'contact_person', 'phone', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'notification_type', 'created_at']
    list_filter = ['is_read', 'notification_type']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'created_at']
    list_filter = ['action']
    search_fields = ['action', 'model_name']
