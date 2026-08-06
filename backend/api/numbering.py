"""
Hujjat va zayavka raqamlari.

Raqam mavjud eng katta qiymatdan davom etadi, sanoqdan emas — yozuv
o'chirilsa ham raqam qayta ishlatilmaydi.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Document


def next_sequence_number(queryset, field_name, prefix):
    """
    `prefix` bilan boshlanadigan eng katta raqamdan keyingisini qaytaradi.

    Ilgari raqam `count() + 1` bilan yig'ilardi. Bitta yozuv o'chirilishi
    bilan sanoq orqaga qaytar va keyingi yozuv allaqachon band raqamni
    so'rar edi — unique cheklovi buzilib, foydalanuvchi 500 olardi. Mavjud
    eng katta qiymatdan hisoblash raqamni faqat oldinga suradi.
    """
    highest = 0
    existing = queryset.filter(**{f"{field_name}__startswith": prefix}).values_list(
        field_name, flat=True
    )
    for value in existing:
        tail = value[len(prefix):]
        if tail.isdigit():
            highest = max(highest, int(tail))
    return highest + 1


def build_document_number(doc_type):
    prefix_map = {
        "purchase_request": "XR",
        "contract": "SH",
        "invoice": "INV",
    }
    prefix = f"{prefix_map.get(doc_type, 'DOC')}-{timezone.now().year}-"
    return f"{prefix}{next_sequence_number(Document.objects, 'doc_number', prefix):04d}"


def save_with_unique_number(save):
    """
    `save(...)` ni raqam to'qnashuvida qayta chaqiradi.

    Raqam o'qish va yozish o'rtasida boshqa so'rov o'sha raqamni band qilib
    ulgurishi mumkin. Bunda IntegrityError qaytadi — qayta urinish yangi
    raqamni oladi.
    """
    last_error = None
    for _ in range(5):
        try:
            with transaction.atomic():
                return save()
        except IntegrityError as exc:
            last_error = exc
    raise last_error
