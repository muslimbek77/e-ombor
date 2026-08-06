"""Xarid buyurtmalari — hujjatning material qatorlari."""


from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from ..audit import create_audit_log
from ..freeze import ensure_document_editable
from ..models import PurchaseOrder
from ..roles import PURCHASE_ORDER_ROLES, is_admin
from ..scope import branch_scope
from ..serializers import (
    PurchaseOrderCreateSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderUpdateSerializer,
)


# --- Purchase Order Views ---
def _purchase_order_write_allowed(user):
    return is_admin(user) or bool(set(user.roles or []).intersection(PURCHASE_ORDER_ROLES))


class PurchaseOrderListView(generics.ListCreateAPIView):
    """Xarid buyurtmalari ro'yxati va yaratish."""

    def get_serializer_class(self):
        return PurchaseOrderCreateSerializer if self.request.method == "POST" else PurchaseOrderSerializer

    def get_queryset(self):
        return branch_scope(
            PurchaseOrder.objects.select_related("document", "document__branch", "supplier")
            .prefetch_related("items__material"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def create(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasi yaratish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Hujjat muzlagan bo'lsa unga yangi material qatorlarini ilib qo'yish ham
        # yopiq — aks holda hujjatning o'zi qulflanadi-yu, summani belgilaydigan
        # qatorlar ochiq qolardi.
        ensure_document_editable(serializer.validated_data["document"])
        with transaction.atomic():
            purchase_order = serializer.save()

        create_audit_log(
            request,
            "purchase_order_created",
            "PurchaseOrder",
            purchase_order.id,
            {"document_id": purchase_order.document_id, "supplier_id": purchase_order.supplier_id},
        )
        return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Xarid buyurtmasi tafsilotlari, tahrirlash va o'chirish."""

    def get_serializer_class(self):
        return PurchaseOrderUpdateSerializer if self.request.method in ("PUT", "PATCH") else PurchaseOrderSerializer

    def get_queryset(self):
        return branch_scope(
            PurchaseOrder.objects.select_related("document", "document__branch", "supplier")
            .prefetch_related("items__material"),
            self.request.user,
            "document__branch",
        )

    def update(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasini tahrirlash uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ensure_document_editable(instance.document)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            purchase_order = serializer.save()

        create_audit_log(
            request,
            "purchase_order_updated",
            "PurchaseOrder",
            purchase_order.id,
            {"supplier_id": purchase_order.supplier_id},
        )
        return Response(PurchaseOrderSerializer(purchase_order).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not _purchase_order_write_allowed(request.user):
            return Response(
                {"error": "Xarid buyurtmasini o'chirish uchun sizda ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()
        ensure_document_editable(instance.document)
        # `doc_number` ni ham yozamiz: buyurtma o'chgach jurnal uni bazadan topa
        # olmaydi va nomni shu yerdan oladi (serializers.AUDIT_DETAIL_LABEL_KEYS).
        create_audit_log(
            request,
            "purchase_order_deleted",
            "PurchaseOrder",
            instance.id,
            {"document_id": instance.document_id, "doc_number": instance.document.doc_number},
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
