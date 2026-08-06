"""
Muzlatish — zanjirga kirgan hujjat o'zgarmaydi.

403 emas, 409: gap ruxsatda emas, hujjatning holatida. Holatlar ro'yxati
`workflow.py: EDITABLE_STATUSES` da.
"""

from rest_framework import exceptions, status

from .models import Document
from .workflow import is_editable


class DocumentFrozen(exceptions.APIException):
    """Zanjirga kirgan hujjatni o'zgartirishga urinish — 409."""

    status_code = status.HTTP_409_CONFLICT


# Xato xabaridagi holatlar ro'yxati qo'lda yozilmaydi: `EDITABLE_STATUSES` ga
# `revision` qo'shilganda xabar eskirib qolgan edi va foydalanuvchiga mavjud
# yo'lni ko'rsatmasdi. Endi u zanjirning o'zidan hosil bo'ladi.
EDITABLE_STATUS_LABELS = ", ".join(
    label for value, label in Document.STATUSES if is_editable(value)
)


def ensure_document_editable(document):
    """
    Hujjat tahrirlanadigan holatdami — aks holda `DocumentFrozen`.

    Ilgari holat umuman tekshirilmasdi: tasdiqlangan, hatto `closed` hujjatning
    summasi ham o'zgartirilishi mumkin edi. Bunda arxitektura, rais va nazorat
    bergan tasdiqlar aslida boshqa hujjatga berilgan bo'lib qolardi va
    zanjirning butun qiymati yo'qolardi. Xato topilsa yo'l: bosqichdagi mas'ul
    `return` qiladi (yoki `reject`), egasi tuzatib qayta yuboradi — bu izohi va
    tarixi bilan qayd etiladi.

    403 emas, 409: gap ruxsatda emas, hujjatning holatida. Hatto admin ham
    `closed` hujjatni tahrirlay olmaydi.
    """
    if not is_editable(document.status):
        raise DocumentFrozen(
            f"{document.doc_number} hujjati «{document.get_status_display()}» holatida — "
            f"tahrirlash faqat {EDITABLE_STATUS_LABELS} holatlarida mumkin"
        )
