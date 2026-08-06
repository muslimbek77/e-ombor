"""Ombor zaxirasi va materiallar harakati."""

from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit import create_audit_log
from ..exports import export_to_csv
from ..models import InventoryItem, StockMovement
from ..notifications import create_low_stock_notifications
from ..roles import can_manage_stock, is_admin
from ..scope import branch_scope, filter_by_query_params
from ..serializers import (
    InventoryAdjustmentSerializer,
    InventoryItemSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
)
from ..stock import (
    InsufficientStockError,
    ensure_sufficient_stock,
    lock_inventory_item,
)


# --- Inventory Views ---
class InventoryListView(generics.ListCreateAPIView):
    """Ombor zaxiralari ro'yxati."""
    serializer_class = InventoryItemSerializer
    
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
