"""Murojaatlar va ishlab chiqarish zayavkalari."""


from django.utils import timezone
from rest_framework import exceptions, generics, serializers
from rest_framework.views import APIView

from ..audit import create_audit_log
from ..exports import export_to_csv
from ..models import ProductionRequest, Ticket
from ..notifications import notify_branch_roles
from ..numbering import next_sequence_number, save_with_unique_number
from ..roles import PRODUCTION_REQUEST_STATUS_ROLES, TICKET_MANAGE_ROLES, has_any_role, is_admin
from ..scope import branch_scope, filter_by_query_params
from ..serializers import ProductionRequestSerializer, TicketSerializer


# --- Production Request Views ---
class ProductionRequestListView(generics.ListCreateAPIView):
    """Ishlab chiqarish zayavkalari ro'yxati."""
    serializer_class = ProductionRequestSerializer
    
    def get_queryset(self):
        return branch_scope(
            ProductionRequest.objects.select_related("site", "site__branch", "created_by"),
            self.request.user,
            "site__branch",
        ).order_by("-created_at")
    
    def perform_create(self, serializer):
        prefix = f"PR-{timezone.localdate().strftime('%Y%m%d')}-"
        save_with_unique_number(
            lambda: serializer.save(
                created_by=self.request.user,
                request_number=(
                    f"{prefix}"
                    f"{next_sequence_number(ProductionRequest.objects, 'request_number', prefix):04d}"
                ),
            )
        )


class ProductionRequestDetailView(generics.RetrieveUpdateAPIView):
    """Ishlab chiqarish zayavka tafsilotlari."""
    serializer_class = ProductionRequestSerializer

    def get_queryset(self):
        return branch_scope(
            ProductionRequest.objects.select_related("site", "site__branch", "created_by"),
            self.request.user,
            "site__branch",
        ).order_by("-created_at")

    def update(self, request, *args, **kwargs):
        self._ensure_can_manage(self.get_object(), request)
        return super().update(request, *args, **kwargs)

    @staticmethod
    def _ensure_can_manage(instance, request):
        """
        KIM va QAYSI HOLATDA — hujjat uchun ishlatilgan qolipning o'zi.

        Muallif (odatda prorab) zayavkasini faqat `pending` holatida
        tahrirlaydi, va `status` maydonini o'zi o'zgartira olmaydi — aks
        holda o'zi yozgan zayavkani o'zi tasdiqlagan bo'lardi.
        """
        user = request.user
        is_manager = has_any_role(user, PRODUCTION_REQUEST_STATUS_ROLES)
        is_author = instance.created_by_id == user.id

        if not (is_manager or is_author):
            raise exceptions.PermissionDenied("Bu zayavkani tahrirlash uchun sizda ruxsat yo'q")
        if "status" in request.data and not is_manager:
            raise exceptions.PermissionDenied("Zayavka holatini o'zgartirish uchun sizda ruxsat yo'q")
        if not is_manager and instance.status != "pending":
            raise exceptions.PermissionDenied("Zayavka faqat 'kutilmoqda' holatida tahrirlanadi")


# --- Ticket Views ---
class TicketListView(generics.ListCreateAPIView):
    """Murojaatlar ro'yxati."""
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        qs = branch_scope(
            Ticket.objects.select_related('created_by', 'assigned_to', 'branch', 'site'),
            self.request.user,
        ).order_by('-created_at')

        return filter_by_query_params(
            qs,
            self.request,
            {"status": "status", "priority": "priority", "category": "category"},
        )

    def perform_create(self, serializer):
        site = serializer.validated_data.get("site")
        if site and not is_admin(self.request.user) and self.request.user.branch_id and site.branch_id != self.request.user.branch_id:
            raise serializers.ValidationError("Siz faqat o'z filiali obyektiga murojaat yarata olasiz")

        ticket = serializer.save(
            created_by=self.request.user,
            branch=serializer.validated_data.get("branch") or (site.branch if site else self.request.user.branch),
        )
        create_audit_log(
            self.request,
            "ticket_created",
            "Ticket",
            ticket.id,
            {
                "branch_id": ticket.branch_id,
                "priority": ticket.priority,
                "status": ticket.status,
            },
        )
        notify_branch_roles(
            ticket.branch,
            {"branch_manager", "admin"},
            "Yangi murojaat yaratildi",
            f"{ticket.title} nomli murojaat yaratildi.",
            "info",
        )


class TicketDetailView(generics.RetrieveUpdateAPIView):
    """Murojaat tafsilotlari."""
    serializer_class = TicketSerializer

    def get_queryset(self):
        return branch_scope(
            Ticket.objects.select_related('created_by', 'assigned_to', 'branch', 'site'),
            self.request.user,
        ).order_by('-created_at')

    def update(self, request, *args, **kwargs):
        self._ensure_can_manage(self.get_object(), request)
        return super().update(request, *args, **kwargs)

    @staticmethod
    def _ensure_can_manage(instance, request):
        """
        Muallif murojaatining mazmunini (sarlavha, tavsif va h.k.) tahrirlaydi.
        `status`, `response` va `assigned_to` — javob berish va yo'naltirish —
        muallifning qo'lida emas, aks holda filialdagi istalgan xodim begona
        murojaatni o'zi "yechildi" deb yopib qo'yardi.
        """
        user = request.user
        is_manager = has_any_role(user, TICKET_MANAGE_ROLES)
        is_author = instance.created_by_id == user.id

        if not (is_manager or is_author):
            raise exceptions.PermissionDenied("Bu murojaatni tahrirlash uchun sizda ruxsat yo'q")
        if not is_manager and set(request.data) & {"status", "response", "assigned_to"}:
            raise exceptions.PermissionDenied(
                "Holat, javob va mas'ul xodimni faqat administrator yoki filial rahbari o'zgartira oladi"
            )


class TicketsExportView(APIView):
    """Murojaatlarni CSV eksport qilish."""

    def get(self, request):
        user = request.user
        queryset = Ticket.objects.select_related("created_by", "assigned_to", "branch", "site").order_by("-created_at")

        if not is_admin(user):
            if user.branch_id:
                queryset = queryset.filter(branch=user.branch)
            else:
                queryset = queryset.filter(created_by=user)

        queryset = filter_by_query_params(
            queryset,
            request,
            {"status": "status", "priority": "priority", "category": "category"},
        )

        rows = [
            {
                "title": ticket.title,
                "category": ticket.get_category_display(),
                "priority": ticket.get_priority_display(),
                "status": ticket.get_status_display(),
                "branch": ticket.branch.name if ticket.branch else "",
                "site": ticket.site.name if ticket.site else "",
                "created_by": ticket.created_by.full_name if ticket.created_by else "",
                "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else "",
                "created_at": timezone.localtime(ticket.created_at).strftime("%Y-%m-%d %H:%M"),
            }
            for ticket in queryset
        ]
        return export_to_csv(
            "tickets-export.csv",
            ["title", "category", "priority", "status", "branch", "site", "created_by", "assigned_to", "created_at"],
            rows,
        )
