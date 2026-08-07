"""
Migratsiyadan oldin yaratilgan bildirishnomalarga `related_type`/`related_id`
ni orqaga qarab to'ldiradi — bosilganda faqat yangi bildirishnomalar emas,
barchasi tegishli sahifaga olib borishi uchun.

Xabar matnidan hujjat/invoice raqami yoki tegishli obyekt ismi ajratib
olinadi va shu bo'yicha qidiriladi — bu tarixiy yozuvlar uchun bir martalik
"eng yaxshi urinish" ishlov berish, kelajakdagi bildirishnomalar endi
yaratilishning o'zida to'g'ridan-to'g'ri belgilanadi.
"""

import re

from django.db import migrations

DOC_NUMBER_RE = re.compile(r"^([A-Za-z0-9-]+)")


def backfill(apps, schema_editor):
    Notification = apps.get_model("api", "Notification")
    Document = apps.get_model("api", "Document")
    Ticket = apps.get_model("api", "Ticket")
    Invoice = apps.get_model("api", "Invoice")
    InventoryItem = apps.get_model("api", "InventoryItem")

    document_titles = {
        "Yangi hujjat yaratildi",
        "Hujjat holati yangilandi",
        "Hujjatga yangi izoh",
        "Hujjatingizga izoh yozildi",
        "Qaytarilgan hujjat qayta yuborildi",
        "Hujjat uzoq vaqt kutmoqda",
    }

    document_by_number = {doc.doc_number: doc.id for doc in Document.objects.all()}
    invoice_by_number = {inv.invoice_number: inv.id for inv in Invoice.objects.all()}

    updated = []
    for notification in Notification.objects.filter(related_type__isnull=True):
        related_type = None
        related_id = None

        if notification.title in document_titles:
            match = DOC_NUMBER_RE.match(notification.message)
            if match:
                doc_id = document_by_number.get(match.group(1))
                if doc_id:
                    related_type, related_id = "document", doc_id

        elif notification.title == "Invoice bo'yicha to'lov qayd etildi":
            match = DOC_NUMBER_RE.match(notification.message)
            if match:
                inv_id = invoice_by_number.get(match.group(1))
                if inv_id:
                    related_type, related_id = "invoice", inv_id

        elif notification.title == "Yangi murojaat yaratildi":
            title_match = re.match(r"^(.*) nomli murojaat yaratildi\.$", notification.message)
            if title_match:
                ticket = Ticket.objects.filter(title=title_match.group(1)).first()
                if ticket:
                    related_type, related_id = "ticket", ticket.id

        elif notification.title == "Kam zaxira ogohlantirishi":
            text_match = re.match(
                r"^(.*) materiali (.*) omborida minimal chegaraga tushdi\.$", notification.message
            )
            if text_match:
                material_name, warehouse_name = text_match.groups()
                item = InventoryItem.objects.filter(
                    material__name=material_name, warehouse__name=warehouse_name
                ).first()
                if item:
                    related_type, related_id = "inventory", item.id

        if related_type:
            notification.related_type = related_type
            notification.related_id = related_id
            updated.append(notification)

    if updated:
        Notification.objects.bulk_update(updated, ["related_type", "related_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_notification_related_id_notification_related_type"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
