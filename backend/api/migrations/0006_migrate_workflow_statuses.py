"""
Eski tasdiqlash zanjirini yangisiga ko'chiradi.

Eski:  created → architecture → ceo → approved → contract → payment → delivering → ...
Yangi: created → architecture → ceo → procurement → anticorruption → accountant → delivering → ...

`approved` (rais tasdiqlagan, xaridlar qo'lida) → `procurement`.
`contract` va `payment` — ikkalasi ham buxgalteriya qo'lidagi bosqichlar edi,
ikkalasi ham `accountant` ga tushadi. Shartnoma va hisob-faktura zanjirdan
chiqarildi: ular endi hujjatga biriktiriladigan artefakt, alohida bosqich emas.

Yangi `anticorruption` bosqichiga hech qanday eski hujjat ko'chirilmaydi —
u tasdiqlangan zanjirning o'rtasiga qo'shilgani uchun eski hujjatlar undan
o'tmagan. Ular buxgalteriyadan davom etadi.
"""

from django.db import migrations


FORWARD = {
    "approved": "procurement",
    "contract": "accountant",
    "payment": "accountant",
}

# Orqaga qaytishda `accountant` ning qaysi eski holatdan kelgani noma'lum —
# ikkalasi ham unga tushgan. Eng erkini (`contract`) tanlanadi, chunki u
# oqimda oldinroq: hujjatni bo'lgan joyidan oldinga surish, keyinga emas.
BACKWARD = {
    "procurement": "approved",
    "accountant": "contract",
    "anticorruption": "approved",
}


def _remap(apps, mapping):
    Document = apps.get_model("api", "Document")
    for old_status, new_status in mapping.items():
        Document.objects.filter(status=old_status).update(status=new_status)


def forwards(apps, schema_editor):
    _remap(apps, FORWARD)


def backwards(apps, schema_editor):
    _remap(apps, BACKWARD)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_alter_document_status"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
