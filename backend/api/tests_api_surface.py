"""
API yuzasi: token talab qilinishi, bo'sh bazada har bir ekran ochilishi,
ro'yxat filtrlari va raqam generatsiyasi.
"""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from .tests_base import ROLE_KEYS, BaseAPITestCase

from .models import ConstructionSite, Document, ProductionRequest


class UnauthenticatedAccessTests(BaseAPITestCase):
    """Token bo'lmasa hech qanday ma'lumot chiqmasligi kerak."""

    PROTECTED_ROUTES = [
        "dashboard",
        "analytics-overview",
        "document-list-create",
        "purchase-order-list",
        "material-list",
        "warehouse-list",
        "inventory-list",
        "stock-movement-list",
        "site-list",
        "branch-list",
        "supplier-list",
        "address-list",
        "contract-list",
        "invoice-list",
        "payment-list",
        "production-request-list",
        "ticket-list",
        "notification-list",
        "audit-log-list",
        "user-list",
    ]

    def test_every_route_requires_authentication(self):
        for route in self.PROTECTED_ROUTES:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmptyDatabaseTests(BaseAPITestCase):
    """
    Baza bo'sh bo'lganda (demo ma'lumotlar tozalangandan keyingi holat)
    hech bir ekran 500 bermasligi kerak.
    """

    LIST_ROUTES = [
        "document-list-create",
        "purchase-order-list",
        "material-list",
        "warehouse-list",
        "inventory-list",
        "stock-movement-list",
        "site-list",
        "supplier-list",
        "address-list",
        "contract-list",
        "invoice-list",
        "payment-list",
        "production-request-list",
        "ticket-list",
        "notification-list",
        "audit-log-list",
    ]

    EXPORT_ROUTES = ["document-export", "inventory-export", "ticket-export"]

    def test_list_endpoints_return_empty_pages_for_every_role(self):
        for role in ROLE_KEYS:
            for route in self.LIST_ROUTES:
                with self.subTest(role=role, route=route):
                    self.auth(self.users[role])
                    response = self.client.get(reverse(route))
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertEqual(response.data["count"], 0)

    def test_dashboard_renders_with_no_data(self):
        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.get(reverse("dashboard"))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["total_documents"], 0)
                self.assertEqual(response.data["low_stock_items"], 0)
                self.assertEqual(response.data["payment_summary"]["total_invoiced"], Decimal("0"))
                self.assertEqual(response.data["payment_summary"]["remaining"], Decimal("0"))

    def test_analytics_renders_with_no_data(self):
        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.get(reverse("analytics-overview"))

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["documents_by_type"], [])
                self.assertEqual(response.data["overdue_invoices"], [])
                self.assertEqual(response.data["low_stock_items"], [])

    def test_exports_return_a_header_only_csv(self):
        self.auth(self.users["admin"])
        for route in self.EXPORT_ROUTES:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response["Content-Type"].startswith("text/csv"))

                lines = [line for line in response.content.decode().splitlines() if line.strip()]
                self.assertEqual(len(lines), 1, "Faqat sarlavha qatori qolishi kerak")


class NumberGenerationTests(BaseAPITestCase):
    """
    `doc_number` va `request_number` sanoq (`count() + 1`) asosida yig'iladi.
    Yozuv o'chirilgach sanoq orqaga qaytadi va keyingi yozuv takrorlanuvchi
    raqam bilan yaratilmoqchi bo'ladi — unique cheklovi 500 beradi.
    """

    def test_document_number_survives_a_deletion(self):
        """
        Ikkita hujjat yaratib birinchisini o'chirsak, sanoq 1 ga tushadi va
        keyingi hujjat ikkinchisining raqamini talab qiladi.
        """
        self.auth(self.users["branch_manager"])
        url = reverse("document-list-create")
        payload = {"doc_type": "purchase_request", "title": "Hujjat"}

        first = self.client.post(url, {**payload, "title": "Birinchi"}, format="json")
        second = self.client.post(url, {**payload, "title": "Ikkinchi"}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        Document.objects.filter(id=first.data["id"]).delete()

        third = self.client.post(url, {**payload, "title": "Uchinchi"}, format="json")
        self.assertEqual(
            third.status_code,
            status.HTTP_201_CREATED,
            "O'chirilgan hujjatdan keyin raqam takrorlanmasligi kerak",
        )
        self.assertNotEqual(third.data["doc_number"], second.data["doc_number"])

    def test_document_numbers_are_unique_across_many_creations(self):
        self.auth(self.users["branch_manager"])
        url = reverse("document-list-create")

        numbers = set()
        for index in range(5):
            response = self.client.post(
                url, {"doc_type": "contract", "title": f"Hujjat {index}"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            numbers.add(response.data["doc_number"])

        self.assertEqual(len(numbers), 5)

    def test_production_request_number_survives_a_deletion(self):
        site = ConstructionSite.objects.create(
            name="A obyekti", code="ST-A", branch=self.branch_a
        )

        self.auth(self.users["prorab"])
        url = reverse("production-request-list")
        payload = {"site": site.id, "title": "Zayavka", "description": "50 qop"}

        first = self.client.post(url, {**payload, "title": "Sement"}, format="json")
        second = self.client.post(url, {**payload, "title": "G'isht"}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        ProductionRequest.objects.filter(id=first.data["id"]).delete()

        third = self.client.post(url, {**payload, "title": "Qum"}, format="json")
        self.assertEqual(
            third.status_code,
            status.HTTP_201_CREATED,
            "O'chirilgan zayavkadan keyin raqam takrorlanmasligi kerak",
        )
        self.assertNotEqual(third.data["request_number"], second.data["request_number"])


class ListFilterTests(BaseAPITestCase):
    """Ro'yxat filtrlari barcha rollar uchun bir xil ishlashi kerak."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from .models import Ticket

        cls.open_ticket = Ticket.objects.create(
            title="Ochiq murojaat",
            description="Test",
            category="material",
            priority="high",
            status="open",
            created_by=cls.users["prorab"],
            branch=cls.branch_a,
        )
        cls.closed_ticket = Ticket.objects.create(
            title="Yopiq murojaat",
            description="Test",
            category="technic",
            priority="low",
            status="closed",
            created_by=cls.users["prorab"],
            branch=cls.branch_a,
        )

    def test_ticket_status_filter_applies_to_every_role(self):
        for role in ROLE_KEYS:
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.get(reverse("ticket-list"), {"status": "open"})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    response.data["count"],
                    1,
                    f"{role} uchun status filtri e'tiborga olinmadi",
                )

    def test_ticket_priority_filter_applies_to_admin(self):
        self.auth(self.users["admin"])
        response = self.client.get(reverse("ticket-list"), {"priority": "low"})

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Yopiq murojaat")

    def test_document_search_filters_the_queryset(self):
        Document.objects.create(
            doc_number="XR-2026-0200",
            doc_type="purchase_request",
            title="Sement uchun so'rov",
            created_by=self.users["procurement"],
            branch=self.branch_a,
        )
        Document.objects.create(
            doc_number="XR-2026-0201",
            doc_type="purchase_request",
            title="G'isht uchun so'rov",
            created_by=self.users["procurement"],
            branch=self.branch_a,
        )

        self.auth(self.users["procurement"])
        response = self.client.get(reverse("document-list-create"), {"search": "Sement"})

        self.assertEqual(response.data["count"], 1)
