"""
Hujjat tasdiqlash zanjiri — yagona manba.

Bu qoidalar ilgari ikki joyda takrorlangan edi: `views.py` (haqiqiy tekshiruv)
va `serializers.py` (frontendga `allowed_actions` sifatida qaytadigan ro'yxat).
Ikkalasi bir-biridan uzilib qolsa natija jimgina buziladi — foydalanuvchiga
tugma ko'rinadi, bosilganda 403 keladi, yoki teskarisi. Shuning uchun zanjir
faqat shu faylda ta'riflanadi.

Bosqichlar ikki turga bo'linadi:

  Tasdiqlash bosqichlari  — `approve` / `reject`. Mas'ul rol qaror qabul qiladi.
  Bajarish bosqichlari    — `advance` / `close`. Qaror emas, faktni qayd etish
                            (tovar keldi, ombor qabul qildi).

`admin` har bir to'plamda ochiq yozilgan, garchi `is_admin()` tekshiruvi
baribir birinchi bo'lib ishlasa ham — qoidani o'qiyotgan odam uchun aniqroq.
"""

WORKFLOW_RULES = {
    # Filial rahbari so'rov yaratadi va o'zi arxitekturaga jo'natadi.
    "created": {
        "submit": {
            "next_status": "architecture",
            "roles": {"branch_manager", "prorab", "procurement", "admin"},
        },
    },
    "architecture": {
        "approve": {"next_status": "ceo", "roles": {"architecture", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"architecture", "admin"}},
    },
    "ceo": {
        "approve": {"next_status": "procurement", "roles": {"ceo", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"ceo", "admin"}},
    },
    # Xaridlar bo'limi ombor qoldig'ini ko'rgan holda qaror qabul qiladi.
    "procurement": {
        "approve": {"next_status": "anticorruption", "roles": {"procurement", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"procurement", "admin"}},
    },
    # Korrupsiyaga qarshi nazorat — to'lovdan OLDIN. Keyin tekshirish kech.
    "anticorruption": {
        "approve": {"next_status": "accountant", "roles": {"anticorruption", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"anticorruption", "admin"}},
    },
    "accountant": {
        "approve": {"next_status": "delivering", "roles": {"accountant", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"accountant", "admin"}},
    },
    # `delivering` va `received` da `reject` ataylab yo'q: tovar yo'lga chiqqach
    # yoki omborga kirgach hujjatni rad etish qoldiqni hujjat holatidan
    # ajratib yuborardi.
    "delivering": {"advance": {"next_status": "received", "roles": {"warehouse", "admin"}}},
    "received": {"close": {"next_status": "closed", "roles": {"warehouse", "prorab", "admin"}}},
    # `anticorruption` bu yerda yo'q — u zanjirni qayta boshlata olmaydi.
    "rejected": {
        "reopen": {
            "next_status": "created",
            "roles": {"branch_manager", "prorab", "procurement", "admin"},
        },
    },
}


CONTROL_ROLE = "anticorruption"

# Zanjirda qatnashadigan barcha rollar. Qo'lda sanab chiqilmaydi —
# `WORKFLOW_RULES` dan hosil bo'ladi, ya'ni yangi bosqich qo'shilganda bu
# to'plam o'zi yangilanadi va vazifalar ajratilishi qoidasi eskirmaydi.
CHAIN_ROLES = {
    role
    for stage in WORKFLOW_RULES.values()
    for config in stage.values()
    for role in config["roles"]
}

# Nazorat roli bilan bir foydalanuvchida birga tura olmaydigan rollar (SoD).
# `admin` ham shu yerda: u har bir bosqichni bajara oladi, ya'ni nazorat bilan
# qo'shilsa zanjir bitta odamning qo'lida qoladi.
ROLES_CONFLICTING_WITH_CONTROL = CHAIN_ROLES - {CONTROL_ROLE}

# Hujjat (va uning material qatorlari) faqat shu holatlarda tahrirlanadi.
# Zanjir boshlangach summa yoki qatorlar o'zgarsa, allaqachon berilgan
# tasdiqlar aslida boshqa hujjatga tegishli bo'lib qoladi — tasdiqlash
# zanjirining butun qiymati shunda. Tuzatish yo'li: `reject`, so'ng `reopen`.
EDITABLE_STATUSES = {"created", "rejected"}


def is_editable(status):
    """Hujjat shu holatda tahrirlanadimi."""
    return status in EDITABLE_STATUSES


def allowed_actions_for(status, roles, is_staff=False):
    """Berilgan holat va rol to'plami uchun mumkin bo'lgan amallar ro'yxati."""
    role_set = set(roles or [])
    return [
        action
        for action, config in WORKFLOW_RULES.get(status, {}).items()
        if is_staff or bool(role_set & config["roles"])
    ]
