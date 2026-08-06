"""
Rol to'plamlari va ularni tekshiruvchi funksiyalar — "kim kim".

Bu fayl ataylab `scope.py` dan ajratilgan. Ko'rish doirasi (kim nimani
KO'RADI) va yozish huquqi (kim nimani O'ZGARTIRADI) tizimda ikki xil narsa
va ularni aralashtirmaslik kerak — fayl chegarasi shu qoidani ko'rinadigan
qiladi. To'plamlarning o'zi shu yerda, ular bilan nima qilinishi esa
boshqa joyda: `scope.py` (ko'rish), `permissions.py` (yozish),
`notifications.py` (kimga xabar boradi).
"""


ADMIN_ROLES = {"admin"}
# Tashkilot bo'ylab ko'radigan rollar. Bu FAQAT ko'rish doirasi — yozish
# huquqi quyidagi alohida to'plamlar bilan tekshiriladi va bu yerga bog'liq
# emas. CEO va xaridlar bo'limi barcha filiallar bo'yicha qaror qabul qiladi,
# nazorat roli esa butun tizimni ko'rmasa vazifasini bajara olmaydi.
#
# `architecture` va `accountant` ham shu yerda, va sabab boshqacha: ular
# ZANJIR BOSQICHI. Filialga bog'langanida boshqa filial hujjati ularga
# ko'rinmasdi va zanjir birinchi tasdiqdayoq 404 ga urilib to'xtardi —
# filialda o'z arxitektori yoki buxgalteri bo'lmasa hujjat umuman
# tasdiqlanmasdi. Zanjir bosqichi bo'lgan rol o'z navbatidagi hujjatni
# ko'rishi shart. `warehouse` bu yerda ataylab yo'q: u tovarni jismonan
# qabul qiladi, ya'ni haqiqatan filialga bog'langan.
GLOBAL_SCOPE_ROLES = {"admin", "ceo", "procurement", "anticorruption", "architecture", "accountant"}
ARCHIVE_ROLES = {"admin", "procurement", "branch_manager"}
STOCK_MOVEMENT_ROLES = {"admin", "warehouse"}
# Filial rahbari so'rovni o'zi to'ldiradi — material qatorlarisiz so'rovning
# mazmuni bo'lmaydi.
PURCHASE_ORDER_ROLES = {"admin", "procurement", "branch_manager"}
CONTRACT_ROLES = {"admin", "procurement"}
SUPPLIER_ROLES = {"admin", "procurement"}
INVOICE_ROLES = {"admin", "accountant", "procurement"}
PAYMENT_ROLES = {"admin", "accountant"}
SITE_ROLES = {"admin", "branch_manager", "architecture"}
# Xaridlar bo'limi bu yerda ataylab yo'q. U begona hujjatni o'zi tahrirlamaydi
# va o'chirmaydi — kamchilikni ko'rsa filial rahbariga aytadi, tuzatishni u
# kiritadi. Xaridlarning zanjirdagi ta'siri `procurement` bosqichidagi
# `approve`/`reject` orqali qoladi.
DOCUMENT_MANAGE_ROLES = {"admin", "branch_manager"}
# Zayavka holatini (`pending → approved → delivered/cancelled`) faqat shu
# rollar o'zgartiradi. Muallif (prorab) zayavkani `pending` holatida
# tahrirlaydi, lekin holatni o'zi o'zgartira olmaydi — aks holda o'zi
# yozgan zayavkani o'zi tasdiqlagan bo'lardi.
PRODUCTION_REQUEST_STATUS_ROLES = {"admin", "branch_manager", "procurement"}
# Murojaatning `status`, `response` va `assigned_to` maydonlarini faqat shu
# rollar o'zgartiradi — muallif faqat sarlavha/tavsif kabi mazmunini
# tahrirlaydi, javob yozish yoki mas'ul tayinlash uning qo'lida emas.
TICKET_MANAGE_ROLES = {"admin", "branch_manager"}


def is_admin(user):
    return user.is_staff or bool(ADMIN_ROLES.intersection(user.roles or []))


def has_any_role(user, roles):
    return is_admin(user) or bool(set(user.roles or []).intersection(roles))


def can_manage_stock(user):
    """Zaxira o'zgartiradigan har qanday amal — faqat omborchi va admin."""
    return is_admin(user) or bool(set(user.roles or []).intersection(STOCK_MOVEMENT_ROLES))
