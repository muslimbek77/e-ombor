from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import (
    Address,
    AuditLog,
    ConstructionSite,
    Contract,
    Document,
    DocumentApproval,
    DocumentFile,
    InventoryItem,
    Invoice,
    Material,
    Notification,
    Payment,
    ProductionRequest,
    PurchaseOrder,
    PurchaseOrderItem,
    StockMovement,
    Supplier,
    Ticket,
    Warehouse,
)

# Bog'liqlik tartibida: bolalar avval, ota-onalar keyin.
# Foydalanuvchilar (User), rollar va filiallar (Branch) saqlanadi —
# rollar model konstantasi, filiallar esa User.branch uchun zarur.
DELETION_ORDER = [
    PurchaseOrderItem,
    PurchaseOrder,
    Payment,
    Invoice,
    Contract,
    DocumentFile,
    DocumentApproval,
    StockMovement,
    InventoryItem,
    ProductionRequest,
    Ticket,
    Document,
    Warehouse,
    Material,
    Supplier,
    Address,
    ConstructionSite,
    Notification,
    AuditLog,
]


class Command(BaseCommand):
    help = (
        "Demo/test ma'lumotlarni o'chiradi. Foydalanuvchilar, ularning rollari "
        "va filiallar saqlanadi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hech narsa o'chirmasdan, nima o'chishini ko'rsatadi.",
        )
        parser.add_argument(
            "--keep-media",
            action="store_true",
            help="Yuklangan fayllarni diskda qoldiradi (yozuvlar baribir o'chadi).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        keep_media = options["keep_media"]

        counts = [(model, model.objects.count()) for model in DELETION_ORDER]
        total = sum(count for _, count in counts)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — hech narsa o'chirilmadi."))
        for model, count in counts:
            if count:
                self.stdout.write(f"  {model._meta.db_table}: {count}")
        self.stdout.write(f"Jami: {total} yozuv")

        if dry_run:
            return

        if not keep_media:
            self._delete_media_files()

        with transaction.atomic():
            for model in DELETION_ORDER:
                model.objects.all().delete()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{total} yozuv o'chirildi."))
        self._report_survivors()

    def _delete_media_files(self):
        """DocumentFile yozuvlari o'chishidan oldin diskdagi fayllarni tozalaydi."""
        removed = 0
        for document_file in DocumentFile.objects.all():
            if document_file.file:
                document_file.file.delete(save=False)
                removed += 1
        if removed:
            self.stdout.write(f"  media: {removed} fayl o'chirildi")

    def _report_survivors(self):
        from django.contrib.auth import get_user_model

        from api.models import Branch

        User = get_user_model()
        self.stdout.write("")
        self.stdout.write("Saqlangan ma'lumotlar:")
        self.stdout.write(f"  users: {User.objects.count()}")
        self.stdout.write(f"  branches: {Branch.objects.count()}")
