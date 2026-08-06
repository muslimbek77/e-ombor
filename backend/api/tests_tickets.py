"""
Zayavka (ProductionRequest) va murojaat (Ticket) — KIM va QAYSI HOLATDA.

Ilgari `ProductionRequestDetailView` va `TicketDetailView` faqat filial
bo'yicha filtrlangan edi, hech qanday rol yoki muallif tekshiruvisiz —
prorab o'z zayavkasini `PATCH {"status": "approved"}` bilan o'zi
tasdiqlar, filialdagi istalgan xodim begona murojaatning `status`,
`response` va `assigned_to` sini o'zgartirar edi. Bu hujjat uchun
2-bosqichda yopilgan teshikning aynan o'zi.
"""

from __future__ import annotations

from django.urls import reverse
from rest_framework import status

from .tests_base import ROLE_KEYS, BaseAPITestCase

from .models import ConstructionSite, ProductionRequest, Ticket


class ProductionRequestPermissionTests(BaseAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = ConstructionSite.objects.create(
            code="ST-PR", name="Zayavka obyekti", branch=cls.branch_a
        )

    def _create_request(self, doc_status="pending", author=None):
        return ProductionRequest.objects.create(
            site=self.site,
            request_number=f"PR-TEST-{ProductionRequest.objects.count() + 1}",
            title="Sement zayavkasi",
            status=doc_status,
            created_by=author or self.users["prorab"],
        )

    def test_author_cannot_approve_their_own_request(self):
        """Prorab o'zi yozgan zayavkani o'zi `status` bilan tasdiqlay olmaydi."""
        request_obj = self._create_request(author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("production-request-detail", args=[request_obj.id]),
            {"status": "approved"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, "pending")

    def test_author_edits_content_while_pending(self):
        request_obj = self._create_request(author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("production-request-detail", args=[request_obj.id]),
            {"title": "Yangilangan sarlavha"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_author_cannot_edit_once_no_longer_pending(self):
        request_obj = self._create_request(doc_status="approved", author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("production-request-detail", args=[request_obj.id]),
            {"title": "Boshqa sarlavha"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_cannot_edit_someone_elses_request(self):
        request_obj = self._create_request(author=self.users["prorab"])

        self.auth(self.users["warehouse"])
        response = self.client.patch(
            reverse("production-request-detail", args=[request_obj.id]),
            {"title": "Begona tahrir"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_change_is_limited_to_allowed_roles(self):
        allowed = {"admin", "branch_manager", "procurement"}

        for role in ROLE_KEYS:
            with self.subTest(role=role):
                request_obj = self._create_request(author=self.users["ceo"])
                self.auth(self.users[role])
                response = self.client.patch(
                    reverse("production-request-detail", args=[request_obj.id]),
                    {"status": "approved"},
                    format="json",
                )

                if role in allowed:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TicketPermissionTests(BaseAPITestCase):
    def _create_ticket(self, author=None):
        return Ticket.objects.create(
            title="Beton yetishmayapti",
            description="Test",
            category="material_shortage",
            status="open",
            created_by=author or self.users["prorab"],
            branch=self.branch_a,
        )

    def test_author_edits_ticket_content(self):
        ticket = self._create_ticket(author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"title": "Yangilangan sarlavha"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_author_cannot_close_their_own_ticket(self):
        """Muallif o'z murojaatini o'zi 'yechildi' deb yopa olmaydi."""
        ticket = self._create_ticket(author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"status": "resolved"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "open")

    def test_author_cannot_assign_their_own_ticket(self):
        ticket = self._create_ticket(author=self.users["prorab"])

        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"assigned_to": self.users["warehouse"].id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stranger_in_branch_cannot_touch_someone_elses_ticket(self):
        """Ilgari filialdagi istalgan xodim begona murojaatni tahrirlay olardi."""
        ticket = self._create_ticket(author=self.users["prorab"])

        self.auth(self.users["warehouse"])
        response = self.client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"status": "resolved"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manage_fields_are_limited_to_allowed_roles(self):
        allowed = {"admin", "branch_manager"}

        for role in ROLE_KEYS:
            with self.subTest(role=role):
                ticket = self._create_ticket(author=self.users["ceo"])
                self.auth(self.users[role])
                response = self.client.patch(
                    reverse("ticket-detail", args=[ticket.id]),
                    {"status": "resolved", "response": "Ko'rib chiqildi"},
                    format="json",
                )

                if role in allowed:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_branchless_user_does_not_see_every_branch_ticket(self):
        """`TicketListView` endi `branch_scope()` ishlatadi — o'z filtrini emas."""
        self._create_ticket(author=self.users["prorab"])

        self.auth(self.rootless_user)
        response = self.client.get(reverse("ticket-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_manager_can_manage_a_ticket_they_did_not_create(self):
        ticket = self._create_ticket(author=self.users["prorab"])

        self.auth(self.users["branch_manager"])
        response = self.client.patch(
            reverse("ticket-detail", args=[ticket.id]),
            {"status": "resolved", "response": "Hal qilindi"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
