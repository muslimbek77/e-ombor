"""
Hujjat tasdiqlash zanjiri — yagona manba.

Bu qoidalar ilgari ikki joyda takrorlangan edi: `views/` (haqiqiy tekshiruv)
va `serializers.py` (frontendga `allowed_actions` sifatida qaytadigan ro'yxat).
Ikkalasi bir-biridan uzilib qolsa natija jimgina buziladi — foydalanuvchiga
tugma ko'rinadi, bosilganda 403 keladi, yoki teskarisi. Shuning uchun zanjir
faqat shu faylda ta'riflanadi.

Bosqichlar ikki turga bo'linadi:

  Tasdiqlash bosqichlari  — `approve` / `reject` / `return`. Mas'ul rol qaror
                            qabul qiladi.
  Bajarish bosqichlari    — `advance` / `close`. Qaror emas, faktni qayd etish
                            (tovar keldi, ombor qabul qildi).

`reject` va `return` ning farqi mahsulot ma'nosida: birinchisi "rad etildi",
ikkinchisi "tuzatib qayta yuboring". Ikkalasi ham hujjatni tahrirlanadigan
holatga tushiradi, lekin `return` dan keyin zanjir arxitekturadan qaytadan
boshlanadi — summa yoki qatorlar o'zgargan bo'lsa oldingi tasdiqlar boshqa
hujjatga tegishli bo'lib qoladi, muzlatish aynan shuning uchun kiritilgan.

Uchinchi amal — `send_back` ("bosqichga qaytarish"). U `return` ning yumshoq
varianti emas, boshqa savolga javob beradi:

  `return`     — hujjatning MAZMUNI xato. Faqat muallif tuzata oladi
                 (`EDITABLE_STATUSES`), demak hujjat tahrirlanadi va zanjir
                 boshdan boshlanadi.
  `send_back`  — hujjat to'g'ri, lekin oldingi bosqich QARORI qayta ko'rilishi
                 kerak. Hujjat muzlagan holicha qoladi (nishonlar tasdiqlash
                 bosqichlari, ular `EDITABLE_STATUSES` da yo'q) — mazmun
                 o'zgarmagani uchun undan oldingi tasdiqlar kuchini saqlaydi.

`send_back` dan keyin zanjir odatdagidek OLDINGA yuradi: xaridlarga qaytgan
hujjat qaytadan nazorat va buxgalteriyadan o'tadi. "Qaytgan joyidan davom
etsin" degan qisqartma ataylab qilinmagan — u `anticorruption` ni chetlab
o'tar edi, u esa to'lovdan oldin turishi shart.

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
    # Tuzatishga qaytarilgan hujjat. `created` bilan bir xil amal, lekin alohida
    # holat: ro'yxatda "yangi so'rov" bilan aralashib ketmasligi kerak, va
    # qaytargan foydalanuvchi qayta yuborilganini bilib turishi kerak.
    "revision": {
        "submit": {
            "next_status": "architecture",
            "roles": {"branch_manager", "prorab", "procurement", "admin"},
        },
    },
    "architecture": {
        "approve": {"next_status": "ceo", "roles": {"architecture", "admin"}},
        "return": {"next_status": "revision", "roles": {"architecture", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"architecture", "admin"}},
    },
    "ceo": {
        "approve": {"next_status": "procurement", "roles": {"ceo", "admin"}},
        "return": {"next_status": "revision", "roles": {"ceo", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"ceo", "admin"}},
    },
    # Xaridlar bo'limi ombor qoldig'ini ko'rgan holda qaror qabul qiladi.
    "procurement": {
        "approve": {"next_status": "anticorruption", "roles": {"procurement", "admin"}},
        "return": {"next_status": "revision", "roles": {"procurement", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"procurement", "admin"}},
    },
    # Korrupsiyaga qarshi nazorat — to'lovdan OLDIN. Keyin tekshirish kech.
    "anticorruption": {
        "approve": {"next_status": "accountant", "roles": {"anticorruption", "admin"}},
        "return": {"next_status": "revision", "roles": {"anticorruption", "admin"}},
        "reject": {"next_status": "rejected", "roles": {"anticorruption", "admin"}},
    },
    "accountant": {
        "approve": {"next_status": "delivering", "roles": {"accountant", "admin"}},
        "return": {"next_status": "revision", "roles": {"accountant", "admin"}},
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


def _derive_approval_chain():
    """
    Tasdiqlash bosqichlari haqiqiy tartibda: arxitektura → rais → ... .

    Qo'lda sanalmaydi — `approve` havolalari bo'ylab yurib topiladi, ya'ni
    zanjirga yangi bosqich qo'shilsa yoki tartib o'zgarsa bu ro'yxat o'zi
    yangilanadi. `send_back` nishonlari shundan olinadi va shu sababli hech
    qachon zanjirning haqiqiy tartibidan ajralib qolmaydi.
    """
    chain = []
    status = WORKFLOW_RULES["created"]["submit"]["next_status"]
    while "approve" in WORKFLOW_RULES.get(status, {}):
        chain.append(status)
        status = WORKFLOW_RULES[status]["approve"]["next_status"]
    return tuple(chain)


APPROVAL_CHAIN = _derive_approval_chain()

# Har bir bosqichdan `send_back` qila oladigan nishonlar — faqat O'ZIDAN
# OLDINGI tasdiqlash bosqichlari. Oldinga (o'zidan keyingi bosqichga)
# yuborish yo'q: u tasdiqlashni chetlab o'tish bo'lardi. Arxitektura ro'yxatda
# yo'q — undan oldin tasdiqlash bosqichi yo'q, demak amal ham ko'rinmaydi.
SEND_BACK_TARGETS = {
    stage: APPROVAL_CHAIN[:index]
    for index, stage in enumerate(APPROVAL_CHAIN)
    if index > 0
}

# Amal qoidaga alohida yozilmaydi, `return` dan hosil bo'ladi: kim tuzatishga
# qaytara olsa, o'sha oldingi bosqichga ham qaytara oladi. `next_status`
# yagona emas — u so'rovda keladi va `targets` bo'yicha tekshiriladi.
for _stage, _targets in SEND_BACK_TARGETS.items():
    WORKFLOW_RULES[_stage]["send_back"] = {
        "next_status": None,
        "roles": WORKFLOW_RULES[_stage]["return"]["roles"],
        "targets": _targets,
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
# zanjirining butun qiymati shunda. Tuzatish yo'li: `return` (yoki `reject`),
# so'ng tuzatib qayta `submit`.
EDITABLE_STATUSES = {"created", "revision", "rejected"}

# Izohsiz bajarilmaydigan amallar. Ikkalasi ham hujjatni orqaga qaytaradi —
# nima tuzatilishi kerakligini aytmasdan qaytarish foydalanuvchini boshi
# berk ko'chaga olib boradi.
COMMENT_REQUIRED_ACTIONS = {
    "reject": "Rad etishda sabab kiritish majburiy",
    "return": "Tuzatishga qaytarishda sabab kiritish majburiy",
    "send_back": "Bosqichga qaytarishda sabab kiritish majburiy",
}


# Dashboard'dagi "tasdiqni kutayotgan hujjatlar" — qaror kutilayotgan barcha
# holatlar: `approve` mavjud bo'lgan navbatdagi bosqichlar, va ulardan
# `return` bilan qaytarilgan `revision`. Qo'lda sanalmagan — `WORKFLOW_RULES`
# dan hosil bo'ladi, aks holda yangi bosqich qo'shilganda ro'yxat eskiradi.
PENDING_APPROVAL_STATUSES = {
    stage for stage, actions in WORKFLOW_RULES.items() if "approve" in actions
} | {
    config["next_status"]
    for stage in WORKFLOW_RULES.values()
    for action, config in stage.items()
    if action == "return"
}


# Kimningdir qarorini kutayotgan holatlar — muallif emas, boshqa rol
# navbatda. `WORKFLOW_RULES` dagi barcha bosqichlar, `EDITABLE_STATUSES`dan
# tashqari (ular muallif tarafida). Uzoq kutgan hujjatlarni topish uchun
# ishlatiladi (`management/commands/escalate_stale_documents.py`).
WAITING_STATUSES = set(WORKFLOW_RULES) - EDITABLE_STATUSES


def is_editable(status):
    """Hujjat shu holatda tahrirlanadimi."""
    return status in EDITABLE_STATUSES


def send_back_targets_for(status):
    """Shu bosqichdan qaysi bosqichlarga qaytarish mumkin (tartib bo'yicha)."""
    return SEND_BACK_TARGETS.get(status, ())


def allowed_actions_for(status, roles, is_staff=False):
    """Berilgan holat va rol to'plami uchun mumkin bo'lgan amallar ro'yxati."""
    role_set = set(roles or [])
    return [
        action
        for action, config in WORKFLOW_RULES.get(status, {}).items()
        if is_staff or bool(role_set & config["roles"])
    ]
