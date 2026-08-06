"""Rol matritsasi — kim nima yoza oladi."""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from .tests_base import ROLE_KEYS, BaseAPITestCase

from .models import Branch, Contract, Document, Invoice, Supplier


class ReferenceDataPermissionTests(BaseAPITestCase):
    """
    Ma'lumotnoma bazasi (filial, material, ombor, yetkazib beruvchi, manzil)
    hammaga ochiq bo'lmasligi kerak — bularni faqat admin boshqaradi.
    """

    def _post(self, route, payload):
        return self.client.post(reverse(route), payload, format="json")

    def test_only_admin_can_create_a_branch(self):
        payload = {"name": "Yangi filial", "code": "BR-NEW"}

        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self._post("branch-list", {**payload, "code": f"BR-{role}"})

                if role == "admin":
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_admin_can_delete_a_branch(self):
        """Filial o'chsa, unga bog'langan foydalanuvchilar filialsiz qoladi."""
        target = Branch.objects.create(name="O'chiriladigan", code="BR-DEL")
        url = reverse("branch-detail", args=[target.id])

        self.auth(self.users["prorab"])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Branch.objects.filter(id=target.id).exists())

    def test_only_admin_can_create_a_material(self):
        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self._post(
                    "material-list",
                    {"name": f"Material {role}", "code": f"MAT-{role}", "unit": "dona"},
                )

                if role == "admin":
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_admin_can_create_a_warehouse(self):
        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self._post(
                    "warehouse-list",
                    {"name": f"Ombor {role}", "code": f"WH-{role}", "branch": self.branch_a.id},
                )

                if role == "admin":
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_writes_are_limited_to_procurement_and_admin(self):
        allowed = {"admin", "procurement"}

        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self._post(
                    "supplier-list",
                    {"name": f"Ta'minotchi {role}", "code": f"SUP-{role}"},
                )

                if role in allowed:
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FinancePermissionTests(BaseAPITestCase):
    """Hisob-faktura va to'lovlar — buxgalteriya hududi."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.supplier = Supplier.objects.create(name="Ta'minotchi", code="SUP-1")
        cls.document = cls._make_document("XR-2026-0001")
        cls.contract = Contract.objects.create(
            document=cls.document,
            supplier=cls.supplier,
            contract_number="SH-001",
            signed_date="2026-01-01",
            total_amount=Decimal("1000.00"),
        )

    @classmethod
    def _make_document(cls, doc_number):
        return Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title=f"Hujjat {doc_number}",
            created_by=cls.users["procurement"],
            branch=cls.branch_a,
            total_amount=Decimal("1000.00"),
        )

    def test_invoice_creation_is_limited_to_finance_roles(self):
        allowed = {"admin", "accountant", "procurement"}

        for index, role in enumerate(ROLE_KEYS):
            with self.subTest(role=role):
                # Invoice.document — OneToOne, shuning uchun har bir rolga alohida hujjat.
                document = self._make_document(f"XR-2026-01{index:02d}")
                self.auth(self.users[role])
                response = self.client.post(
                    reverse("invoice-list"),
                    {
                        "document": document.id,
                        "contract": self.contract.id,
                        "invoice_number": f"INV-{index:03d}",
                        "invoice_date": "2026-02-01",
                        "due_date": "2026-03-01",
                        "total_amount": "500.00",
                    },
                    format="json",
                )

                if role in allowed:
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_registration_is_limited_to_finance_roles(self):
        allowed = {"admin", "accountant"}
        invoice = Invoice.objects.create(
            document=self.document,
            contract=self.contract,
            invoice_number="INV-PAY",
            invoice_date="2026-02-01",
            due_date="2026-03-01",
            total_amount=Decimal("10000.00"),
        )
        url = reverse("payment-create", args=[invoice.id])

        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.post(url, {"amount": "100.00"}, format="json")

                if role in allowed:
                    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_cannot_exceed_the_invoice_total(self):
        invoice = Invoice.objects.create(
            document=self.document,
            contract=self.contract,
            invoice_number="INV-OVER",
            invoice_date="2026-02-01",
            due_date="2026-03-01",
            total_amount=Decimal("100.00"),
        )

        self.auth(self.users["accountant"])
        response = self.client.post(
            reverse("payment-create", args=[invoice.id]), {"amount": "150.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
