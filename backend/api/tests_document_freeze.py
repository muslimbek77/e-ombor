"""
Muzlatish: zanjirga kirgan hujjat va uning material qatorlari o'zgarmaydi.
"""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import Document, Material, PurchaseOrder, Supplier


class DocumentFreezeTests(BaseAPITestCase):
    """
    Zanjirga kirgan hujjat muzlaydi.

    Ilgari holat umuman tekshirilmasdi: tasdiqlangan, hatto `closed` hujjatning
    summasi ham o'zgartirilishi mumkin edi — ya'ni arxitektura, rais va nazorat
    bergan tasdiq aslida boshqa hujjatga tegishli bo'lib qolardi.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.supplier = Supplier.objects.create(name="Ta'minotchi", code="SUP-FR")
        cls.material = Material.objects.create(name="Sement", code="MAT-FR", unit="qop")

    def _create_document(self, doc_number, doc_status="created"):
        return Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Muzlatish testi",
            created_by=self.users["branch_manager"],
            branch=self.branch_a,
            status=doc_status,
            total_amount=Decimal("1000.00"),
        )

    def test_editable_statuses_accept_changes(self):
        for index, doc_status in enumerate(("created", "revision", "rejected")):
            with self.subTest(status=doc_status):
                document = self._create_document(f"XR-2026-04{index:02d}", doc_status)

                self.auth(self.users["branch_manager"])
                response = self.client.patch(
                    reverse("document-detail", args=[document.id]),
                    {"total_amount": "2000.00"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_document_in_the_chain_cannot_be_edited(self):
        frozen = ["architecture", "ceo", "procurement", "anticorruption", "accountant", "delivering", "received", "closed"]

        for index, doc_status in enumerate(frozen):
            with self.subTest(status=doc_status):
                document = self._create_document(f"XR-2026-05{index:02d}", doc_status)

                self.auth(self.users["branch_manager"])
                response = self.client.patch(
                    reverse("document-detail", args=[document.id]),
                    {"total_amount": "9999.00"},
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
                document.refresh_from_db()
                self.assertEqual(document.total_amount, Decimal("1000.00"))

    def test_the_freeze_message_names_every_editable_status(self):
        """
        Xabar foydalanuvchiga mavjud yo'lni ko'rsatadi. `EDITABLE_STATUSES` ga
        yangi holat qo'shilib xabar eskirsa, u yolg'on maslahat beradi —
        shuning uchun ro'yxat qo'lda emas, zanjirdan hosil bo'ladi.
        """
        from .workflow import EDITABLE_STATUSES

        document = self._create_document("XR-2026-0610", "closed")

        self.auth(self.users["branch_manager"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "X"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        message = str(response.data["detail"])
        for editable in EDITABLE_STATUSES:
            label = dict(Document.STATUSES)[editable]
            self.assertIn(label, message, f"«{label}» xabarda yo'q — xabar eskirgan")

    def test_closed_document_cannot_be_deleted(self):
        document = self._create_document("XR-2026-0600", "closed")

        self.auth(self.users["branch_manager"])
        response = self.client.delete(reverse("document-detail", args=[document.id]))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Document.objects.filter(id=document.id).exists())

    def test_admin_is_not_exempt_from_the_freeze(self):
        """Gap ruxsatda emas, hujjatning holatida — shuning uchun 409, 403 emas."""
        document = self._create_document("XR-2026-0601", "closed")

        self.auth(self.users["admin"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "Yangi nom"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        document.refresh_from_db()
        self.assertEqual(document.title, "Muzlatish testi")

    def test_permission_is_checked_before_the_freeze(self):
        """Begona hujjatga 403 — muzlatish uni 409 ga aylantirib yubormasin."""
        document = self._create_document("XR-2026-0602", "closed")

        self.auth(self.users["accountant"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "Yangi nom"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _purchase_order_payload(self, document):
        return {
            "document": document.id,
            "supplier": self.supplier.id,
            "items": [{"material": self.material.id, "quantity": "10.00", "unit_price": "100.00"}],
        }

    def test_purchase_order_follows_the_document_freeze(self):
        """
        Hujjat muzlab, material qatorlari ochiq qolsa muzlatishning ma'nosi
        yo'q — summani aynan shu qatorlar belgilaydi.
        """
        document = self._create_document("XR-2026-0700", "created")

        self.auth(self.users["branch_manager"])
        created = self.client.post(
            reverse("purchase-order-list"), self._purchase_order_payload(document), format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        document.status = "accountant"
        document.save(update_fields=["status"])
        url = reverse("purchase-order-detail", args=[created.data["id"]])

        update = self.client.patch(url, {"supplier": self.supplier.id}, format="json")
        self.assertEqual(update.status_code, status.HTTP_409_CONFLICT)

        delete = self.client.delete(url)
        self.assertEqual(delete.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(PurchaseOrder.objects.filter(id=created.data["id"]).count(), 1)

    def test_purchase_order_cannot_be_attached_to_a_frozen_document(self):
        document = self._create_document("XR-2026-0701", "ceo")

        self.auth(self.users["branch_manager"])
        response = self.client.post(
            reverse("purchase-order-list"), self._purchase_order_payload(document), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(PurchaseOrder.objects.count(), 0)
