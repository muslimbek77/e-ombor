"""
Ruxsat sinflari — kim nimani YOZA oladi.

Ko'rish doirasi bu yerda emas: u `scope.py` da. Rol to'plamlarining o'zi
`roles.py` da.

Bu yerdagi `ControlRoleReadOnly` `settings.REST_FRAMEWORK` dagi
`DEFAULT_PERMISSION_CLASSES` orqali barcha view'ga qo'llanadi. Uni har bir
view'da alohida sanab chiqish ataylab qilinmagan: bitta view unutilsa nazorat
roli aynan o'sha teshikdan yozib ketardi, va bunday xato ko'rinmaydi — hech
kim shikoyat qilmaydi, chunki taqiq ishlamayotgani sezilmaydi.
"""

from rest_framework import permissions

from .roles import (
    ADMIN_ROLES,
    INVOICE_ROLES,
    PAYMENT_ROLES,
    SITE_ROLES,
    SUPPLIER_ROLES,
    has_any_role,
)
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


# Qo'shimcha ruxsat sinfi kerak bo'lgan view'lar uchun. DRF'da `permission_classes`
# e'lon qilinsa `DEFAULT_PERMISSION_CLASSES` butunlay almashadi — nazorat rolining
# yozish taqiqi ham shu bilan tushib qolardi. Shuning uchun qo'shimcha sinf shu
# to'plamning USTIGA qo'shiladi, o'rniga emas.
DEFAULT_PERMISSIONS = (permissions.IsAuthenticated, ControlRoleReadOnly)


class RoleGatedWrite(permissions.BasePermission):
    """
    O'qish hammaga (autentifikatsiyadan o'tganlarga), yozish esa faqat
    `write_roles` dagi rollarga ochiq.

    Ma'lumotnoma bazasi — filial, material, ombor, obyekt, yetkazib beruvchi —
    ilgari hech qanday rol tekshiruvisiz edi: istalgan xodim material qo'sha,
    ombor tahrirlay yoki filialni butunlay o'chira olardi (filial o'chsa unga
    bog'langan foydalanuvchilar filialsiz qolardi).
    """

    write_roles = ADMIN_ROLES
    message = "Bu bo'limni o'zgartirish uchun sizda ruxsat yo'q"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return has_any_role(request.user, self.write_roles)


class AdminOnlyWrite(RoleGatedWrite):
    write_roles = ADMIN_ROLES


class SupplierWrite(RoleGatedWrite):
    write_roles = SUPPLIER_ROLES
    message = "Yetkazib beruvchini o'zgartirish uchun sizda ruxsat yo'q"


class SiteWrite(RoleGatedWrite):
    write_roles = SITE_ROLES
    message = "Qurilish obyektini o'zgartirish uchun sizda ruxsat yo'q"


class InvoiceWrite(RoleGatedWrite):
    write_roles = INVOICE_ROLES
    message = "Hisob-fakturani o'zgartirish uchun sizda ruxsat yo'q"


class PaymentWrite(RoleGatedWrite):
    write_roles = PAYMENT_ROLES
    message = "To'lov qayd etish uchun sizda ruxsat yo'q"
