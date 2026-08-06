"""
Nazorat roli: global yozish taqiqi va vazifalar ajratilishi (SoD).
"""

from __future__ import annotations


from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase, User

from .models import ConstructionSite, Document, Notification, ProductionRequest


class ControlRoleReadOnlyTests(BaseAPITestCase):
    """
    Nazorat roli (`anticorruption`) tizimda hech nimani o'zgartirmaydi.

    Ilgari taqiq passiv edi — nazorat hech qaysi yozish to'plamida yo'q edi,
    lekin hujjat, zayavka va murojaat yaratish hamma rolga ochiqligicha
    qolgandi va u shu yo'ldan yozib ketardi.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = ConstructionSite.objects.create(name="A obyekti", code="ST-CR", branch=cls.branch_a)
        cls.document = Document.objects.create(
            doc_number="XR-2026-0300",
            doc_type="purchase_request",
            title="Nazorat testi",
            created_by=cls.users["branch_manager"],
            branch=cls.branch_a,
        )

    def test_control_role_cannot_create_a_document(self):
        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("document-list-create"),
            {"doc_type": "purchase_request", "title": "Nazorat hujjati"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Document.objects.filter(title="Nazorat hujjati").exists())

    def test_control_role_cannot_create_a_production_request(self):
        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("production-request-list"),
            {"site": self.site.id, "title": "Zayavka", "description": "50 qop"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProductionRequest.objects.count(), 0)

    def test_control_role_cannot_create_a_ticket(self):
        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("ticket-list"),
            {"title": "Murojaat", "description": "Test", "category": "material", "priority": "low"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_every_write_endpoint_is_closed_for_the_control_role(self):
        """Yozish yo'llari bittalab emas, ro'yxat bo'yicha tekshiriladi."""
        cases = [
            ("post", reverse("document-list-create"), {"doc_type": "purchase_request", "title": "X"}),
            ("patch", reverse("document-detail", args=[self.document.id]), {"title": "O'zgargan"}),
            ("delete", reverse("document-detail", args=[self.document.id]), None),
            ("post", reverse("document-archive-toggle", args=[self.document.id]), {"archive": True}),
            ("post", reverse("document-file-upload", args=[self.document.id]), None),
            ("post", reverse("purchase-order-list"), {"document": self.document.id}),
            ("post", reverse("material-list"), {"name": "M", "code": "M-1", "unit": "dona"}),
            ("post", reverse("warehouse-list"), {"name": "W", "code": "W-1", "branch": 1}),
            ("post", reverse("branch-list"), {"name": "B", "code": "B-1"}),
            ("post", reverse("supplier-list"), {"name": "S", "code": "S-1"}),
            ("post", reverse("address-list"), {"name": "A"}),
            ("post", reverse("site-list"), {"name": "O", "code": "O-1"}),
            ("post", reverse("stock-movement-list"), {"movement_type": "IN"}),
            ("post", reverse("contract-list"), {"document": self.document.id}),
            ("post", reverse("invoice-list"), {"document": self.document.id}),
            ("post", reverse("ticket-list"), {"title": "T", "description": "T", "category": "material"}),
            ("post", reverse("production-request-list"), {"site": self.site.id, "title": "Z"}),
            ("post", reverse("user-list"), {"email": "x@test.uz", "password": "TestParol123!"}),
        ]

        self.auth(self.users["anticorruption"])
        for method, url, payload in cases:
            with self.subTest(method=method, url=url):
                request = getattr(self.client, method)
                response = request(url, payload, format="json") if payload else request(url)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f"{method.upper()} {url} nazorat roliga ochiq qolgan",
                )

    def test_control_role_still_reads_everything(self):
        """Taqiq faqat yozishga tegishli — ko'rish doirasi eng kengi bo'lib qoladi."""
        self.auth(self.users["anticorruption"])

        for route in ("document-list-create", "audit-log-list", "inventory-list", "invoice-list"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, status.HTTP_200_OK)

        detail = self.client.get(reverse("document-detail", args=[self.document.id]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

    def test_control_role_can_still_decide_at_its_own_stage(self):
        """Yagona ish-mazmunli istisno — workflow endpointi."""
        self.document.status = "anticorruption"
        self.document.save(update_fields=["status"])

        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("document-workflow", args=[self.document.id]),
            {"action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accountant")

    def test_workflow_exception_does_not_open_other_stages(self):
        """Istisno endpointga berilgan, zanjirga emas — rol tekshiruvi joyida."""
        self.document.status = "ceo"
        self.document.save(update_fields=["status"])

        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("document-workflow", args=[self.document.id]),
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_control_role_keeps_its_own_account_actions(self):
        """
        O'z hisobiga tegishli amallar ish ma'lumoti emas. Ular ham yopilsa
        nazorat roli tizimdan chiqa ham, parolini almashtira ham olmasdi.
        """
        notification = Notification.objects.create(
            user=self.users["anticorruption"], title="Xabar", message="Test"
        )

        self.auth(self.users["anticorruption"])
        self.assertEqual(
            self.client.post(reverse("notification-read", args=[notification.id])).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.patch(reverse("user_profile"), {"phone": "+998900000000"}, format="json").status_code,
            status.HTTP_200_OK,
        )

        tokens = self.login("anticorruption@test.uz").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(
            self.client.post(reverse("logout"), {"refresh": tokens["refresh"]}, format="json").status_code,
            status.HTTP_200_OK,
        )

    def test_every_view_carries_the_global_write_guard(self):
        """
        Taqiq `DEFAULT_PERMISSION_CLASSES` da turadi, lekin DRF'da view o'z
        `permission_classes` ini e'lon qilsa default butunlay almashadi. Ya'ni
        bitta view'da unutilgan `views.DEFAULT_PERMISSIONS` taqiqni jimgina
        o'chiradi — bu test aynan shuni ushlaydi.
        """
        from rest_framework.permissions import AllowAny

        from .permissions import ControlRoleReadOnly
        from .urls import urlpatterns

        for pattern in urlpatterns:
            view = getattr(pattern.callback, "cls", None)
            if view is None:
                continue
            with self.subTest(view=view.__name__):
                classes = tuple(view.permission_classes)
                if AllowAny in classes:
                    continue  # login / refresh / register — autentifikatsiyagacha
                self.assertIn(
                    ControlRoleReadOnly,
                    classes,
                    f"{view.__name__} nazorat taqiqini yo'qotgan — `DEFAULT_PERMISSIONS` qo'shilsin",
                )


class ControlRoleSeparationTests(BaseAPITestCase):
    """
    Vazifalar ajratilishi: nazorat roli zanjirning boshqa roli bilan
    birlashsa, u o'zi tekshiradigan jarayonning ishtirokchisiga aylanadi.
    """

    def _create_user(self, payload):
        self.auth(self.users["admin"])
        return self.client.post(reverse("user-list"), payload, format="json")

    def test_control_role_cannot_be_combined_on_creation(self):
        for conflicting in ("procurement", "ceo", "branch_manager", "admin", "warehouse"):
            with self.subTest(role=conflicting):
                response = self._create_user(
                    {
                        "email": f"nazorat.{conflicting}@test.uz",
                        "password": "TestParol123!",
                        "first_name": "Nazorat",
                        "last_name": "Testov",
                        "roles": ["anticorruption", conflicting],
                    }
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("roles", response.data)
                self.assertFalse(User.objects.filter(email=f"nazorat.{conflicting}@test.uz").exists())

    def test_control_role_alone_is_accepted(self):
        response = self._create_user(
            {
                "email": "nazorat.yolgiz@test.uz",
                "password": "TestParol123!",
                "first_name": "Nazorat",
                "last_name": "Yolg'iz",
                "roles": ["anticorruption"],
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="nazorat.yolgiz@test.uz").roles, ["anticorruption"])

    def test_control_role_cannot_be_combined_with_is_staff(self):
        """`is_staff` rol emas, lekin `is_admin()` uchun roldan farqi yo'q."""
        response = self._create_user(
            {
                "email": "nazorat.staff@test.uz",
                "password": "TestParol123!",
                "first_name": "Nazorat",
                "last_name": "Staff",
                "roles": ["anticorruption"],
                "is_staff": True,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_staff", response.data)

    def test_chain_role_cannot_be_added_to_a_control_user(self):
        self.auth(self.users["admin"])
        response = self.client.patch(
            reverse("user-detail", args=[self.users["anticorruption"].id]),
            {"roles": ["anticorruption", "accountant"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.users["anticorruption"].refresh_from_db()
        self.assertEqual(self.users["anticorruption"].roles, ["anticorruption"])

    def test_control_role_cannot_be_added_to_a_chain_user(self):
        """Teskari yo'nalish ham yopiq — buxgalterga nazorat roli qo'shilmaydi."""
        self.auth(self.users["admin"])
        response = self.client.patch(
            reverse("user-detail", args=[self.users["accountant"].id]),
            {"roles": ["accountant", "anticorruption"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.users["accountant"].refresh_from_db()
        self.assertEqual(self.users["accountant"].roles, ["accountant"])

    def test_partial_update_sees_the_resulting_state(self):
        """
        PATCH da `roles` yuborilmasa mavjud qiymat qoladi — `is_staff` ni
        alohida yoqib nazoratni adminga aylantirib bo'lmasligi kerak.
        """
        self.auth(self.users["admin"])
        response = self.client.patch(
            reverse("user-detail", args=[self.users["anticorruption"].id]),
            {"is_staff": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.users["anticorruption"].refresh_from_db()
        self.assertFalse(self.users["anticorruption"].is_staff)
