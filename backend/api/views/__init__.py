"""
View'lar paketi — domen bo'yicha bo'lingan.

Ilgari hammasi bitta `views.py` da edi (2000+ qator): kerakli joyni topish
uchun butun faylni o'qishga to'g'ri kelardi. Bo'lish mantiqni o'zgartirmadi —
`urls.py` va testlar shu paketdan avvalgidek `views.X` ko'rinishida oladi,
chunki quyida hammasi qayta eksport qilinadi.

Yordamchi funksiyalar bu yerda emas: rol to'plamlari `roles.py`, ko'rish
doirasi `scope.py`, ruxsat sinflari `permissions.py`, qolganlari
`audit.py` / `notifications.py` / `numbering.py` / `freeze.py` / `stock.py` /
`exports.py` da.
"""

from .auth import (  # noqa: F401
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    UserDetailView,
    UserListView,
    UserProfileView,
    UserRegisterView,
)
from .dashboard import (  # noqa: F401
    AnalyticsOverviewView,
    DashboardView,
)
from .documents import (  # noqa: F401
    DocumentArchiveToggleView,
    DocumentCommentListCreateView,
    DocumentDetailView,
    DocumentFileListView,
    DocumentFileUploadView,
    DocumentListCreateView,
    DocumentWorkflowActionView,
    DocumentsExportView,
)
from .purchases import (  # noqa: F401
    PurchaseOrderDetailView,
    PurchaseOrderListView,
)
from .inventory import (  # noqa: F401
    InventoryExportView,
    InventoryListView,
    InventoryUpdateView,
    StockMovementListView,
)
from .reference import (  # noqa: F401
    AddressDetailView,
    AddressListView,
    BranchDetailView,
    BranchListView,
    ConstructionSiteDetailView,
    ConstructionSiteListView,
    MaterialDetailView,
    MaterialListView,
    SupplierDetailView,
    SupplierListView,
    WarehouseDetailView,
    WarehouseListView,
)
from .finance import (  # noqa: F401
    ContractDetailView,
    ContractListView,
    InvoiceDetailView,
    InvoiceListView,
    PaymentCreateView,
    PaymentListView,
)
from .tickets import (  # noqa: F401
    ProductionRequestDetailView,
    ProductionRequestListView,
    TicketDetailView,
    TicketListView,
    TicketsExportView,
)
from .notifications import (  # noqa: F401
    AuditLogListView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)

__all__ = [
    "AddressDetailView",
    "AddressListView",
    "AnalyticsOverviewView",
    "AuditLogListView",
    "BranchDetailView",
    "BranchListView",
    "ChangePasswordView",
    "ConstructionSiteDetailView",
    "ConstructionSiteListView",
    "ContractDetailView",
    "ContractListView",
    "CustomTokenObtainPairView",
    "CustomTokenRefreshView",
    "DashboardView",
    "DocumentArchiveToggleView",
    "DocumentCommentListCreateView",
    "DocumentDetailView",
    "DocumentFileListView",
    "DocumentFileUploadView",
    "DocumentListCreateView",
    "DocumentWorkflowActionView",
    "DocumentsExportView",
    "InventoryExportView",
    "InventoryListView",
    "InventoryUpdateView",
    "InvoiceDetailView",
    "InvoiceListView",
    "LogoutView",
    "MaterialDetailView",
    "MaterialListView",
    "NotificationListView",
    "NotificationMarkAllReadView",
    "NotificationMarkReadView",
    "PaymentCreateView",
    "PaymentListView",
    "ProductionRequestDetailView",
    "ProductionRequestListView",
    "PurchaseOrderDetailView",
    "PurchaseOrderListView",
    "StockMovementListView",
    "SupplierDetailView",
    "SupplierListView",
    "TicketDetailView",
    "TicketListView",
    "TicketsExportView",
    "UserDetailView",
    "UserListView",
    "UserProfileView",
    "UserRegisterView",
    "WarehouseDetailView",
    "WarehouseListView",
]
