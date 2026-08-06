"""Dashboard va analitika — faqat agregatsiya, yozish yo'q."""

from decimal import Decimal

from django.db.models import F, Q, Sum, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit import scoped_audit_logs
from ..models import (
    ConstructionSite,
    Document,
    InventoryItem,
    Invoice,
    Material,
    Notification,
    Ticket,
    Warehouse,
)
from ..scope import branch_scope
from ..workflow import PENDING_APPROVAL_STATUSES
from ..serializers import (
    AuditLogSerializer,
    DocumentSerializer,
    InventoryItemSerializer,
    InvoiceSerializer,
    NotificationSerializer,
    TicketSerializer,
)


class DashboardView(APIView):
    """Dashboard statistikalari."""
    
    def get(self, request):
        user = request.user

        documents = branch_scope(Document.objects.select_related("created_by", "site", "branch"), user)
        sites = branch_scope(ConstructionSite.objects.select_related("branch", "prorab"), user)
        warehouses = branch_scope(Warehouse.objects.select_related("branch"), user)
        inventory = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            user,
            "warehouse__branch",
        )
        tickets = branch_scope(
            Ticket.objects.select_related("created_by", "assigned_to", "branch", "site"),
            user,
        )
        invoices = branch_scope(
            Invoice.objects.select_related("document", "contract", "document__branch"),
            user,
            "document__branch",
        )

        payment_summary = invoices.aggregate(
            total_invoiced=Sum("total_amount"),
            total_paid=Sum("paid_amount"),
        )
        total_invoiced = payment_summary["total_invoiced"] or Decimal("0")
        total_paid = payment_summary["total_paid"] or Decimal("0")

        stats = {
            "total_documents": documents.count(),
            "pending_approvals": documents.filter(status__in=PENDING_APPROVAL_STATUSES).count(),
            "total_materials": Material.objects.count(),
            "total_warehouses": warehouses.count(),
            "total_sites": sites.count(),
            "low_stock_items": inventory.filter(
                Q(quantity__lte=F("min_quantity")) | Q(min_quantity=0, quantity__lte=10)
            ).count(),
            "recent_documents": DocumentSerializer(documents.order_by("-created_at")[:5], many=True).data,
            "recent_tickets": TicketSerializer(tickets.order_by("-created_at")[:5], many=True).data,
            "notifications": NotificationSerializer(
                Notification.objects.filter(user=user).order_by("-created_at")[:10],
                many=True,
            ).data,
            "document_status_breakdown": list(
                documents.values("status").annotate(total=Count("id")).order_by("status")
            ),
            "payment_summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "remaining": total_invoiced - total_paid,
            },
            "site_budget_summary": {
                "total_budget": sites.aggregate(total=Sum("budget"))["total"] or Decimal("0"),
            },
        }

        return Response(stats, status=status.HTTP_200_OK)


class AnalyticsOverviewView(APIView):
    """Analytics va hisobotlar uchun agregatsiya endpointi."""

    def get(self, request):
        user = request.user
        documents = branch_scope(Document.objects.select_related("branch", "site"), user)
        inventory = branch_scope(
            InventoryItem.objects.select_related("warehouse", "warehouse__branch", "material"),
            user,
            "warehouse__branch",
        )
        tickets = branch_scope(Ticket.objects.select_related("branch", "site"), user)
        invoices = branch_scope(
            Invoice.objects.select_related("document", "document__branch"),
            user,
            "document__branch",
        )
        audit_logs = scoped_audit_logs(user)

        overdue_invoices = invoices.filter(payment_status__in=["unpaid", "partial"], due_date__lt=timezone.localdate())
        low_stock_items = inventory.filter(Q(quantity__lte=F("min_quantity")) | Q(min_quantity=0, quantity__lte=10))

        data = {
            "documents_by_type": list(documents.values("doc_type").annotate(total=Count("id")).order_by("doc_type")),
            "documents_by_status": list(documents.values("status").annotate(total=Count("id")).order_by("status")),
            "tickets_by_priority": list(tickets.values("priority").annotate(total=Count("id")).order_by("priority")),
            "tickets_by_status": list(tickets.values("status").annotate(total=Count("id")).order_by("status")),
            "overdue_invoices": InvoiceSerializer(overdue_invoices.order_by("due_date")[:10], many=True).data,
            "low_stock_items": InventoryItemSerializer(low_stock_items.order_by("quantity")[:10], many=True).data,
            "recent_audit_logs": AuditLogSerializer(audit_logs[:10], many=True).data,
        }
        return Response(data, status=status.HTTP_200_OK)
