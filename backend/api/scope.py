"""
Ko'rish doirasi — kim qaysi yozuvlarni ko'radi.

Yozish huquqi bilan aralashtirmaslik kerak: u `roles.py` dagi to'plamlar
bilan alohida tekshiriladi va bu yerdagi kengaytirilgan doira uni
kengaytirmaydi.
"""

from .roles import GLOBAL_SCOPE_ROLES, is_admin


def branch_scope(queryset, user, field_name="branch"):
    """
    Natijani foydalanuvchi filiali bilan cheklaydi.

    Filialsiz foydalanuvchi bo'sh natija oladi. Ilgari bu holat filtrni
    butunlay o'chirar edi, ya'ni `/auth/register/` orqali ochilgan yangi
    hisob (filiali yo'q) barcha filiallarning hujjatlari, shartnomalari va
    to'lovlarini ko'ra olardi.

    `GLOBAL_SCOPE_ROLES` — istisno: markaziy rollar (rais, xaridlar, nazorat)
    barcha filiallarni ko'radi. Ular ko'pincha filialga biriktirilmaydi, va
    bu istisnosiz filialsiz hisob sifatida hech nima ko'rmay qolardi.
    """
    if is_admin(user) or set(user.roles or []) & GLOBAL_SCOPE_ROLES:
        return queryset
    if not user.branch_id:
        return queryset.none()
    return queryset.filter(**{field_name: user.branch})


def filter_by_query_params(queryset, request, mapping):
    for param, field_name in mapping.items():
        value = request.query_params.get(param)
        if value:
            queryset = queryset.filter(**{field_name: value})
    return queryset
