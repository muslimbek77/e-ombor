"""
Ma'lumotnoma bazasi: material, ombor, obyekt, filial, yetkazib beruvchi, manzil.

Ilgari bu bo'lim hech qanday rol tekshiruvisiz edi — istalgan xodim filialni
o'chira olardi. Yozish darvozalari `permissions.py` dagi `RoleGatedWrite`
oilasida.
"""

from rest_framework import generics

from ..models import (
    Address,
    Branch,
    ConstructionSite,
    Material,
    Supplier,
    Warehouse,
)
from ..permissions import (
    AdminOnlyWrite,
    DEFAULT_PERMISSIONS,
    SiteWrite,
    SupplierWrite,
)
from ..scope import branch_scope
from ..serializers import (
    AddressSerializer,
    BranchSerializer,
    ConstructionSiteSerializer,
    MaterialSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)


# --- Material Views ---
class MaterialListView(generics.ListCreateAPIView):
    """Materiallar ro'yxati va yaratish."""
    serializer_class = MaterialSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Material.objects.all()


class MaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Material tahrirlash va o'chirish."""
    serializer_class = MaterialSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Material.objects.all()


# --- Warehouse Views ---
class WarehouseListView(generics.ListCreateAPIView):
    """Omborxonalar ro'yxati va yaratish."""
    serializer_class = WarehouseSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Warehouse.objects.select_related("branch").all()

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user)


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Omborxona tahrirlash va o'chirish."""
    serializer_class = WarehouseSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Warehouse.objects.select_related("branch").all()

    def get_queryset(self):
        # Ro'yxat filial bo'yicha filtrlanadi — tafsilot ham shunday bo'lishi
        # kerak, aks holda id ni taxmin qilib begona filial omborini o'qish,
        # tahrirlash va o'chirish mumkin edi.
        return branch_scope(super().get_queryset(), self.request.user)


# --- Construction Site Views ---
class ConstructionSiteListView(generics.ListCreateAPIView):
    """Qurilish obyektlari ro'yxati va yaratish."""
    serializer_class = ConstructionSiteSerializer
    permission_classes = DEFAULT_PERMISSIONS + (SiteWrite,)
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
    permission_classes = DEFAULT_PERMISSIONS + (SiteWrite,)
    queryset = ConstructionSite.objects.select_related("branch", "prorab")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user)


# --- Branch Views ---
class BranchListView(generics.ListCreateAPIView):
    """Filiallar ro'yxati."""
    serializer_class = BranchSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Branch.objects.all().order_by("name")


class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Filial tahrirlash va o'chirish."""
    serializer_class = BranchSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Branch.objects.all()


# --- Supplier Views ---
class SupplierListView(generics.ListCreateAPIView):
    """Etkazib beruvchilar ro'yxati."""
    serializer_class = SupplierSerializer
    permission_classes = DEFAULT_PERMISSIONS + (SupplierWrite,)
    queryset = Supplier.objects.all().order_by("name")


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Etkazib beruvchi tahrirlash va o'chirish."""
    serializer_class = SupplierSerializer
    permission_classes = DEFAULT_PERMISSIONS + (SupplierWrite,)
    queryset = Supplier.objects.all()


# --- Address Views ---
class AddressListView(generics.ListCreateAPIView):
    """Manzillar ro'yxati."""
    serializer_class = AddressSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Address.objects.all()


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manzil tahrirlash va o'chirish."""
    serializer_class = AddressSerializer
    permission_classes = DEFAULT_PERMISSIONS + (AdminOnlyWrite,)
    queryset = Address.objects.all()
