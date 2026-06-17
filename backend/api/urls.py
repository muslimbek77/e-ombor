from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth
    path('auth/register/', views.UserRegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/user/', views.UserProfileView.as_view(), name='user_profile'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Documents
    path('documents/', views.DocumentListCreateView.as_view(), name='document-list-create'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    
    # Document Files
    path('documents/<int:doc_pk>/files/', views.DocumentFileUploadView.as_view(), name='document-file-upload'),
    path('documents/<int:doc_pk>/files/list/', views.DocumentFileListView.as_view(), name='document-file-list'),
    
    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase-order-list'),
    
    # Materials
    path('materials/', views.MaterialListView.as_view(), name='material-list'),
    path('materials/<int:pk>/', views.MaterialDetailView.as_view(), name='material-detail'),
    
    # Warehouses
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    
    # Inventory
    path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:pk>/', views.InventoryUpdateView.as_view(), name='inventory-update'),
    
    # Construction Sites
    path('sites/', views.ConstructionSiteListView.as_view(), name='site-list'),
    path('sites/<int:pk>/', views.ConstructionSiteDetailView.as_view(), name='site-detail'),
    
    # Branches
    path('branches/', views.BranchListView.as_view(), name='branch-list'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),
    
    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Addresses
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    
    # Contracts
    path('contracts/', views.ContractListView.as_view(), name='contract-list'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),
    
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('invoices/<int:invoice_pk>/payments/', views.PaymentCreateView.as_view(), name='payment-create'),
    
    # Production Requests
    path('production-requests/', views.ProductionRequestListView.as_view(), name='production-request-list'),
    path('production-requests/<int:pk>/', views.ProductionRequestDetailView.as_view(), name='production-request-detail'),
    
    # Tickets (Support)
    path('tickets/', views.TicketListView.as_view(), name='ticket-list'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='ticket-detail'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', views.NotificationMarkAllReadView.as_view(), name='notification-all-read'),
]
