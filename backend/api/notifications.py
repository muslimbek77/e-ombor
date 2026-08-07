"""
Bildirishnomalar.

`notify_branch_roles` markaziy rollarni filialdan qat'i nazar qo'shadi —
ular ko'pincha filialga biriktirilmaydi va aks holda zanjirdagi o'z
navbatlarini xabarsiz kutib qolardi.
"""

from decimal import Decimal

from .models import Notification, User
from .roles import GLOBAL_SCOPE_ROLES, is_admin


def notify_users(users, title, message, notification_type="info", related_type=None, related_id=None):
    unique_users = []
    seen_ids = set()
    for user in users:
        if user and user.id not in seen_ids:
            unique_users.append(user)
            seen_ids.add(user.id)

    Notification.objects.bulk_create(
        [
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                related_type=related_type,
                related_id=related_id,
            )
            for user in unique_users
        ]
    )


def notify_branch_roles(branch, roles, title, message, notification_type="info", related_type=None, related_id=None):
    """
    Filialdagi tegishli rollarga xabar yuboradi.

    Markaziy rollar (rais, xaridlar, nazorat) ko'pincha filialga biriktirilmaydi
    — ular filial bo'yicha filtrda umuman topilmasdi va zanjirdagi o'z
    navbatlarini xabarsiz kutib qolardi. Shuning uchun ular filialdan qat'i
    nazar qo'shiladi.
    """
    if not branch:
        return

    wanted = set(roles)
    # `roles` — JSONField, uni bazada ishonchli filtrlab bo'lmaydi (SQLite va
    # PostgreSQL da sintaksis boshqacha), shuning uchun saralash Python'da.
    # Ichki tizim, foydalanuvchilar soni kichik — bu qabul qilinadigan narx.
    filtered = [
        user
        for user in User.objects.filter(is_active=True).only("id", "roles", "branch", "is_staff")
        if is_admin(user)
        or (
            bool(set(user.roles or []) & wanted)
            and (user.branch_id == branch.id or bool(set(user.roles or []) & GLOBAL_SCOPE_ROLES))
        )
    ]
    if filtered:
        notify_users(filtered, title, message, notification_type, related_type, related_id)


def create_low_stock_notifications(item):
    threshold = item.min_quantity or Decimal("10")
    if item.quantity > threshold:
        return

    title = "Kam zaxira ogohlantirishi"
    message = f"{item.material.name} materiali {item.warehouse.name} omborida minimal chegaraga tushdi."
    notify_branch_roles(
        item.warehouse.branch,
        {"warehouse", "branch_manager", "admin"},
        title,
        message,
        "warning",
        related_type="inventory",
        related_id=item.id,
    )
