"""
Uzoq vaqt bir holatda qotib qolgan hujjatlar haqida mas'ul rollarga eslatma.

Zanjirda hujjat kimningdir stolida "unutilib qolishi" mumkin — masalan filialda
omborchi bo'lmasa `delivering` holatida abadiy qoladi. Bu buyruq shunday
hujjatlarni topib, o'sha bosqichda harakat qila oladigan rollarga (va filial
rahbari/administratorga) eslatma yuboradi. Kron yoki boshqa rejalashtiruvchi
orqali muntazam ishga tushirilishi mo'ljallangan — o'zi hech narsani
rejalashtirmaydi.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Document
from ...notifications import notify_branch_roles
from ...workflow import WAITING_STATUSES, WORKFLOW_RULES

STALE_THRESHOLD_DAYS = 3


class Command(BaseCommand):
    help = "Belgilangan muddatdan ko'p vaqt bir holatda qolgan hujjatlar haqida mas'ul rollarga eslatma yuboradi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=STALE_THRESHOLD_DAYS,
            help=f"Necha kundan beri o'zgarmagan hujjatlar eslatma olishi kerak (standart: {STALE_THRESHOLD_DAYS}).",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        stale_documents = Document.objects.filter(
            status__in=WAITING_STATUSES,
            updated_at__lt=cutoff,
            is_archived=False,
        ).select_related("branch")

        count = 0
        for document in stale_documents:
            responsible_roles = {
                role
                for config in WORKFLOW_RULES.get(document.status, {}).values()
                for role in config["roles"]
            }
            notify_branch_roles(
                document.branch,
                responsible_roles | {"branch_manager", "admin"},
                "Hujjat uzoq vaqt kutmoqda",
                (
                    f"{document.doc_number} hujjati \"{document.get_status_display()}\" "
                    f"holatida {options['days']} kundan ortiq harakatsiz qolmoqda."
                ),
                "warning",
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} ta hujjat uchun eslatma yuborildi."))
