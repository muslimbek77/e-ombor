"""Audit jurnali — yozish va ko'rish doirasi."""

from django.db.models import Q

from .models import AuditLog
from .roles import is_admin


def create_audit_log(request, action, model_name, object_id=None, details=None):
    AuditLog.objects.create(
        user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details or {},
        ip_address=request.META.get("REMOTE_ADDR"),
    )


def scoped_audit_logs(user):
    queryset = AuditLog.objects.select_related("user").order_by("-created_at")
    if is_admin(user):
        return queryset
    if not user.branch_id:
        # Filialsiz foydalanuvchiga faqat o'z izlari ko'rinadi.
        return queryset.filter(user=user)

    return queryset.filter(
        Q(user__branch=user.branch)
        | Q(details__branch_id=user.branch_id)
    )
