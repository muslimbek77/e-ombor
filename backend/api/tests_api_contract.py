"""
API shartnoma testlari.

Bu to'plam `tests_stock_movements.py` dan farqli o'laroq bitta domenni emas,
butun API yuzasini tekshiradi:

* autentifikatsiya oqimi (register / login / refresh / logout / parol),
* bo'sh bazada har bir ro'yxat endpointi 200 qaytarishi,
* rol matritsasi — kim nima yoza oladi,
* filial izolyatsiyasi — boshqa filial yozuviga kirish yopiqmi,
* raqam generatsiyasi (doc_number, request_number) takrorlanmasligi,
* ro'yxat filtrlari barcha rollar uchun ishlashi.

Testlar to'g'ri (kutilgan) xulqni tasdiqlaydi. Yiqilgan test — tuzatilishi
kerak bo'lgan xato.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Branch,
    ConstructionSite,
    Contract,
    Document,
    Invoice,
    Material,
    ProductionRequest,
    Supplier,
    Warehouse,
)

User = get_user_model()

# Har bir rol uchun bitta foydalanuvchi — matritsa testlari shu kalitlar bilan ishlaydi.
ROLE_KEYS = [
    "admin",
    "ceo",
    "architecture",
    "procurement",
    "accountant",
    "warehouse",
    "prorab",
    "branch_manager",
]


class BaseAPITestCase(APITestCase):
    """Ikkita filial va har bir rol uchun foydalanuvchi tayyorlaydi."""

    @classmethod
    def setUpTestData(cls):
        cls.branch_a = Branch.objects.create(name="Filial A", code="BR-A")
        cls.branch_b = Branch.objects.create(name="Filial B", code="BR-B")

        cls.users = {}
        for role in ROLE_KEYS:
            cls.users[role] = User.objects.create_user(
                email=f"{role}@test.uz",
                password="TestParol123!",
                first_name=role.title(),
                last_name="Testov",
                roles=["admin"] if role == "admin" else [role],
                branch=cls.branch_a,
                is_staff=role == "admin",
                is_superuser=role == "admin",
            )

        # B filialidagi omborchi — izolyatsiya testlari uchun.
        cls.warehouse_user_b = User.objects.create_user(
            email="warehouse.b@test.uz",
            password="TestParol123!",
            first_name="Omborchi",
            last_name="B",
            roles=["warehouse"],
            branch=cls.branch_b,
        )

        # Filialsiz, rolsiz foydalanuvchi — o'zi ro'yxatdan o'tgan holat.
        cls.rootless_user = User.objects.create_user(
            email="rootless@test.uz",
            password="TestParol123!",
            first_name="Filialsiz",
            last_name="Foydalanuvchi",
            roles=[],
            branch=None,
        )

    def auth(self, user):
        """So'rovlarni berilgan foydalanuvchi nomidan yuboradi."""
        self.client.force_authenticate(user=user)
        return user

    def login(self, email, password="TestParol123!"):
        return self.client.post(
            reverse("login"), {"email": email, "password": password}, format="json"
        )


class AuthFlowTests(BaseAPITestCase):
    """Register / login / refresh / logout / parol o'zgartirish."""

    def test_login_returns_token_pair(self):
        response = self.login("admin@test.uz")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_is_rejected(self):
        response = self.login("admin@test.uz", "NotoUgriParol1!")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rotates_the_token(self):
        refresh = self.login("ceo@test.uz").data["refresh"]
        response = self.client.post(reverse("token_refresh"), {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["refresh"], refresh)

    def test_reused_refresh_token_is_rejected(self):
        refresh = self.login("ceo@test.uz").data["refresh"]
        self.client.post(reverse("token_refresh"), {"refresh": refresh}, format="json")

        response = self.client.post(reverse("token_refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_the_refresh_token(self):
        tokens = self.login("ceo@test.uz").data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        logout = self.client.post(reverse("logout"), {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        refresh = self.client.post(
            reverse("token_refresh"), {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_cannot_grant_admin_role(self):
        """Ochiq register endpointi orqali o'ziga rol biriktirib bo'lmaydi."""
        response = self.client.post(
            reverse("register"),
            {
                "email": "buzgunchi@test.uz",
                "password": "TestParol123!",
                "password_confirm": "TestParol123!",
                "first_name": "Buzg'unchi",
                "last_name": "Foydalanuvchi",
                "roles": ["admin"],
            },
            format="json",
        )

        if response.status_code == status.HTTP_201_CREATED:
            created = User.objects.get(email="buzgunchi@test.uz")
            self.assertEqual(
                created.roles,
                [],
                "Register endpointi so'rovdagi rolni biriktirmasligi kerak",
            )
            self.assertFalse(created.is_staff)

    def test_registration_cannot_pick_an_arbitrary_branch(self):
        """Filialni ham tashqaridan tanlab bo'lmaydi — bu filial ma'lumotini ochadi."""
        response = self.client.post(
            reverse("register"),
            {
                "email": "filialchi@test.uz",
                "password": "TestParol123!",
                "password_confirm": "TestParol123!",
                "first_name": "Filial",
                "last_name": "Tanlovchi",
                "branch": self.branch_b.id,
            },
            format="json",
        )

        if response.status_code == status.HTTP_201_CREATED:
            created = User.objects.get(email="filialchi@test.uz")
            self.assertIsNone(
                created.branch,
                "Register endpointi so'rovdagi filialni biriktirmasligi kerak",
            )

    def test_change_password_requires_the_old_one(self):
        self.auth(self.users["ceo"])
        response = self.client.post(
            reverse("change_password"),
            {"old_password": "NotoUgri1!", "new_password": "YangiParol123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_updates_the_credentials(self):
        self.auth(self.users["ceo"])
        response = self.client.post(
            reverse("change_password"),
            {"old_password": "TestParol123!", "new_password": "YangiParol123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.users["ceo"].refresh_from_db()
        self.assertTrue(self.users["ceo"].check_password("YangiParol123!"))


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


class BranchIsolationTests(BaseAPITestCase):
    """
    Ro'yxat endpointlari filial bo'yicha filtrlanadi — tafsilot endpointlari
    ham xuddi shunday yopiq bo'lishi kerak.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.warehouse_b = Warehouse.objects.create(
            name="B ombori", code="WH-B", branch=cls.branch_b
        )
        cls.site_b = ConstructionSite.objects.create(
            name="B obyekti", code="ST-B", branch=cls.branch_b
        )
        cls.document_b = Document.objects.create(
            doc_number="XR-2026-9001",
            doc_type="purchase_request",
            title="B filiali hujjati",
            created_by=cls.warehouse_user_b,
            branch=cls.branch_b,
        )

    def test_warehouse_detail_hides_other_branches(self):
        self.auth(self.users["warehouse"])  # A filiali
        response = self.client.get(reverse("warehouse-detail", args=[self.warehouse_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_warehouse_of_another_branch_cannot_be_deleted(self):
        self.auth(self.users["warehouse"])
        response = self.client.delete(reverse("warehouse-detail", args=[self.warehouse_b.id]))

        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.assertTrue(Warehouse.objects.filter(id=self.warehouse_b.id).exists())

    def test_site_detail_hides_other_branches(self):
        self.auth(self.users["prorab"])  # A filiali
        response = self.client.get(reverse("site-detail", args=[self.site_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_document_detail_hides_other_branches(self):
        self.auth(self.users["procurement"])  # A filiali
        response = self.client.get(reverse("document-detail", args=[self.document_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_upload_to_another_branch_document_is_blocked(self):
        self.auth(self.users["procurement"])  # A filiali
        response = self.client.get(
            reverse("document-file-list", args=[self.document_b.id])
        )
        self.assertEqual(response.data["count"], 0)

        upload = self.client.post(
            reverse("document-file-upload", args=[self.document_b.id]), {}, format="multipart"
        )
        self.assertEqual(
            upload.status_code,
            status.HTTP_404_NOT_FOUND,
            "Boshqa filial hujjati ko'rinmasligi kerak — 404",
        )

    def test_branchless_user_does_not_see_every_branch(self):
        """
        `branch_scope` filialsiz foydalanuvchi uchun filtrni butunlay o'chiradi.
        Bu ro'yxatdan o'tgan yangi hisobga butun tizimni ochib beradi.
        """
        self.auth(self.rootless_user)
        response = self.client.get(reverse("document-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["count"],
            0,
            "Filialsiz foydalanuvchiga begona filial hujjatlari ko'rinmasligi kerak",
        )


class DocumentWorkflowTests(BaseAPITestCase):
    """Hujjat holati zanjiri va unga bog'liq ruxsatlar."""

    def _create_document(self, doc_number="XR-2026-0100", branch=None):
        return Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Workflow hujjati",
            created_by=self.users["prorab"],
            branch=branch or self.branch_a,
        )

    def test_full_approval_chain(self):
        document = self._create_document()
        url = reverse("document-workflow", args=[document.id])

        chain = [
            ("prorab", "submit", "architecture"),
            ("architecture", "approve", "ceo"),
            ("ceo", "approve", "approved"),
            ("procurement", "advance", "contract"),
            ("accountant", "advance", "payment"),
            ("accountant", "advance", "delivering"),
            ("warehouse", "advance", "received"),
            ("warehouse", "close", "closed"),
        ]

        for role, action, expected_status in chain:
            with self.subTest(role=role, action=action):
                self.auth(self.users[role])
                response = self.client.post(url, {"action": action}, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["status"], expected_status)

    def test_wrong_role_cannot_advance_the_document(self):
        document = self._create_document("XR-2026-0101")
        document.status = "architecture"
        document.save(update_fields=["status"])

        self.auth(self.users["warehouse"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "approve"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejection_requires_a_comment(self):
        document = self._create_document("XR-2026-0102")
        document.status = "architecture"
        document.save(update_fields=["status"])

        self.auth(self.users["architecture"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "reject"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_deletion_is_limited_to_the_author_and_admin(self):
        """Boshqa rol yaratgan hujjatni ixtiyoriy xodim o'chira olmasligi kerak."""
        document = self._create_document("XR-2026-0103")

        self.auth(self.users["accountant"])
        response = self.client.delete(reverse("document-detail", args=[document.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Document.objects.filter(id=document.id).exists())


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
        self.auth(self.users["procurement"])
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
        self.auth(self.users["procurement"])
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


class UserAdministrationTests(BaseAPITestCase):
    """Foydalanuvchi boshqaruvi faqat adminda."""

    def test_non_admin_cannot_list_users(self):
        for role in ROLE_KEYS:
            if role == "admin":
                continue
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.get(reverse("user-list"))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.auth(self.users["admin"])
        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], User.objects.count())

    def test_admin_cannot_delete_themselves(self):
        self.auth(self.users["admin"])
        response = self.client.delete(reverse("user-detail", args=[self.users["admin"].id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_update_cannot_escalate_roles(self):
        """`/auth/user/` o'z profilini tahrirlaydi — rol u yerdan o'zgarmasligi kerak."""
        self.auth(self.users["prorab"])
        response = self.client.patch(
            reverse("user_profile"), {"roles": ["admin"], "is_staff": True}, format="json"
        )

        self.users["prorab"].refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.users["prorab"].roles, ["prorab"])
        self.assertFalse(self.users["prorab"].is_staff)


class NotificationTests(BaseAPITestCase):
    """Bildirishnomalar faqat egasiga ko'rinadi."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from .models import Notification

        cls.notification = Notification.objects.create(
            user=cls.users["ceo"], title="Shaxsiy xabar", message="Faqat CEO uchun"
        )

    def test_user_sees_only_their_own_notifications(self):
        self.auth(self.users["prorab"])
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.data["count"], 0)

    def test_marking_another_users_notification_is_rejected(self):
        self.auth(self.users["prorab"])
        response = self.client.post(reverse("notification-read", args=[self.notification.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_mark_all_as_read(self):
        self.auth(self.users["ceo"])
        response = self.client.post(reverse("notification-all-read"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
