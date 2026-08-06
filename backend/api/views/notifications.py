"""Bildirishnomalar va audit jurnali ro'yxati."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit import scoped_audit_logs
from ..models import Notification
from ..scope import filter_by_query_params
from ..serializers import AuditLogSerializer, NotificationSerializer
from django.db.models import Q


# --- Notification Views ---
class NotificationListView(generics.ListAPIView):
    """Bildirishnomalar ro'yxati."""
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationMarkReadView(generics.UpdateAPIView):
    """Bildirishnomani o'qilgan deb belgilash."""
    # O'z bildirishnomasi — ish ma'lumoti emas.
    control_role_may_write = True

    def post(self, request, pk=None):
        notification = Notification.objects.filter(
            user=request.user, id=pk
        ).first()
        if notification:
            notification.is_read = True
            notification.save()
            return Response({'message': 'O\'qilgan deb belgilandi'})
        return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllReadView(APIView):
    """Barcha bildirishnomalarni o'qilgan deb belgilash."""
    control_role_may_write = True

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Barcha bildirishnomalar o\'qilgan deb belgilandi'})


class AuditLogListView(generics.ListAPIView):
    """Audit log ro'yxati."""

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = scoped_audit_logs(self.request.user)
        queryset = filter_by_query_params(
            queryset,
            self.request,
            {"action": "action", "model_name": "model_name", "user": "user_id"},
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(action__icontains=search)
                | Q(model_name__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset
