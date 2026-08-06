"""
Global ruxsat sinflari.

Bu yerdagi `ControlRoleReadOnly` `settings.REST_FRAMEWORK` dagi
`DEFAULT_PERMISSION_CLASSES` orqali barcha view'ga qo'llanadi. Uni har bir
view'da alohida sanab chiqish ataylab qilinmagan: bitta view unutilsa nazorat
roli aynan o'sha teshikdan yozib ketardi, va bunday xato ko'rinmaydi — hech
kim shikoyat qilmaydi, chunki taqiq ishlamayotgani sezilmaydi.
"""

from rest_framework import permissions

from .workflow import CONTROL_ROLE


def is_control_user(user):
    """Foydalanuvchida nazorat roli bormi."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return CONTROL_ROLE in (getattr(user, "roles", None) or [])


class ControlRoleReadOnly(permissions.BasePermission):
    """
    Nazorat roli (`anticorruption`) uchun yozish yopiq — u faqat o'qiydi.

    Ilgari himoya passiv edi: nazorat hech qaysi yozish to'plamiga kiritilmagan,
    lekin hujjat, zayavka va murojaat yaratish hamma rolga ochiq bo'lgani uchun
    u baribir ma'lumot kirita olardi. Ma'lumot kiritadigan kuzatuvchi o'zi ham
    jarayon ishtirokchisiga aylanadi va nazorat qiymatini yo'qotadi.

    Istisno — view'da `control_role_may_write = True` bo'lsa. Ikki toifa:

      * `documents/<pk>/workflow/` — nazorat o'z bosqichida qaror qabul qiladi,
        bu uning asosiy vazifasi;
      * o'z hisobiga tegishli amallar (chiqish, parol, profil, bildirishnomani
        o'qilgan deb belgilash) — bular ish ma'lumoti emas, va yopilsa nazorat
        roli tizimdan chiqa ham olmasdi.

    `is_staff` bu yerda imtiyoz bermaydi: taqiqning ma'nosi — uni chetlab
    o'tib bo'lmasligi. Rolni boshqa rol bilan qo'shib berish esa
    `serializers.py` dagi SoD tekshiruvi bilan taqiqlangan.
    """

    message = "Nazorat roli ma'lumotni o'zgartira olmaydi — u faqat o'qiydi"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not is_control_user(request.user):
            return True
        return bool(getattr(view, "control_role_may_write", False))
