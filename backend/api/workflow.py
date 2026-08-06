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


def allowed_actions_for(status, roles, is_staff=False):
    """Berilgan holat va rol to'plami uchun mumkin bo'lgan amallar ro'yxati."""
    role_set = set(roles or [])
    return [
        action
        for action, config in WORKFLOW_RULES.get(status, {}).items()
        if is_staff or bool(role_set & config["roles"])
    ]
