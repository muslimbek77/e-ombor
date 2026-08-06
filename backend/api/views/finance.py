"""Shartnoma, hisob-faktura va to'lov zanjiri."""


from rest_framework import generics, serializers, status
from rest_framework.response import Response

from ..audit import create_audit_log
from ..models import Contract, Invoice, Payment
from ..notifications import notify_users
from ..permissions import DEFAULT_PERMISSIONS, InvoiceWrite, PaymentWrite
from ..roles import CONTRACT_ROLES, is_admin
from ..scope import branch_scope
from ..serializers import (
    ContractSerializer,
    InvoiceSerializer,
    PaymentSerializer,
)


# --- Contract Views ---
def _contract_write_allowed(user):
    return is_admin(user) or bool(set(user.roles or []).intersection(CONTRACT_ROLES))


class ContractListView(generics.ListCreateAPIView):
    """Shartnomalar ro'yxati va yaratish."""
    serializer_class = ContractSerializer

    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def create(self, request, *args, **kwargs):
        if not _contract_write_allowed(request.user):
            return Response(
                {"error": "Shartnoma yaratish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()

        create_audit_log(
            request,
            "contract_created",
            "Contract",
            contract.id,
            {"document_id": contract.document_id, "supplier_id": contract.supplier_id},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContractDetailView(generics.RetrieveUpdateAPIView):
    """Shartnoma tafsilotlari va tahrirlash."""
    serializer_class = ContractSerializer

    def get_queryset(self):
        return branch_scope(
            Contract.objects.select_related("document", "supplier", "document__branch"),
            self.request.user,
            "document__branch",
        ).order_by("-document__created_at")

    def update(self, request, *args, **kwargs):
        if not _contract_write_allowed(request.user):
            return Response(
                {"error": "Shartnomani tahrirlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        contract = serializer.save()

        create_audit_log(request, "contract_updated", "Contract", contract.id, {"supplier_id": contract.supplier_id})
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Invoice Views ---
class InvoiceListView(generics.ListCreateAPIView):
    """Hisob-fakturalar ro'yxati."""
    serializer_class = InvoiceSerializer
    permission_classes = DEFAULT_PERMISSIONS + (InvoiceWrite,)
    queryset = Invoice.objects.select_related("document", "contract", "document__branch").order_by("-invoice_date")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user, "document__branch")


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    """Hisob-faktura tafsilotlari."""
    serializer_class = InvoiceSerializer
    permission_classes = DEFAULT_PERMISSIONS + (InvoiceWrite,)
    queryset = Invoice.objects.select_related("document", "contract", "document__branch").order_by("-invoice_date")

    def get_queryset(self):
        return branch_scope(super().get_queryset(), self.request.user, "document__branch")


# --- Payment Views ---
class PaymentListView(generics.ListAPIView):
    """To'lovlar ro'yxati."""
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        return branch_scope(
            Payment.objects.select_related("invoice", "invoice__document", "invoice__document__branch", "performed_by"),
            self.request.user,
            "invoice__document__branch",
        ).order_by("-payment_date")


class PaymentCreateView(generics.CreateAPIView):
    """To'lov yaratish."""
    serializer_class = PaymentSerializer
    permission_classes = DEFAULT_PERMISSIONS + (PaymentWrite,)
    
    def perform_create(self, serializer):
        invoice_id = self.kwargs.get('invoice_pk')
        invoice = branch_scope(
            Invoice.objects.select_related("document", "document__branch"),
            self.request.user,
            "document__branch",
        ).filter(id=invoice_id).first()
        if not invoice:
            raise serializers.ValidationError("Hisob-faktura topilmadi")

        amount = serializer.validated_data["amount"]
        if amount <= 0:
            raise serializers.ValidationError("To'lov summasi 0 dan katta bo'lishi kerak")
        if invoice.paid_amount + amount > invoice.total_amount:
            raise serializers.ValidationError("To'lov invoice summasidan oshib ketdi")

        payment = serializer.save(invoice=invoice, performed_by=self.request.user)

        invoice.paid_amount += payment.amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.payment_status = "paid"
        elif invoice.paid_amount > 0:
            invoice.payment_status = "partial"
        invoice.save()

        create_audit_log(
            self.request,
            "payment_created",
            "Payment",
            payment.id,
            {"invoice": invoice.invoice_number, "amount": str(payment.amount)},
        )
        notify_users(
            [invoice.document.created_by],
            "Invoice bo'yicha to'lov qayd etildi",
            f"{invoice.invoice_number} uchun {payment.amount} summa to'landi.",
            "success",
        )
