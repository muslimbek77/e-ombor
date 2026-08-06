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
    DocumentComment,
    InventoryItem,
    Invoice,
    Material,
    Notification,
    ProductionRequest,
    PurchaseOrder,
    PurchaseOrderItem,
    StockMovement,
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
    "anticorruption",
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

    def test_global_roles_see_every_branch(self):
        """
        Markaziy rollar barcha filiallarni ko'radi. Ikki sabab:

        * rais, xaridlar va nazorat tashkilot bo'ylab qaror qabul qiladi;
        * arxitektura va buxgalteriya esa ZANJIR BOSQICHI — o'z navbatidagi
          hujjatni ko'ra olmasa zanjir birinchi tasdiqdayoq to'xtab qolardi.
        """
        for role in ("ceo", "procurement", "anticorruption", "architecture", "accountant"):
            with self.subTest(role=role):
                self.auth(self.users[role])  # A filialiga biriktirilgan
                response = self.client.get(reverse("document-detail", args=[self.document_b.id]))
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_procurement_sees_stock_of_every_branch(self):
        """Xaridlar bo'limi qaror qabul qilishda butun ombor holatiga tayanadi."""
        self.auth(self.users["procurement"])
        response = self.client.get(reverse("warehouse-detail", args=[self.warehouse_b.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_global_read_scope_does_not_grant_write(self):
        """Kengaytirilgan ko'rish doirasi yozish huquqini bermaydi."""
        self.auth(self.users["anticorruption"])
        response = self.client.delete(reverse("warehouse-detail", args=[self.warehouse_b.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Warehouse.objects.filter(id=self.warehouse_b.id).exists())

    def test_branch_bound_roles_still_isolated(self):
        """
        Global bo'lmagan rollar uchun izolyatsiya o'zgarmagan.

        `warehouse` ataylab shu ro'yxatda qoladi, garchi u ham zanjir bosqichi
        bo'lsa ham: omborchi tovarni jismonan qabul qiladi, ya'ni uning ishi
        haqiqatan bitta filialda.
        """
        for role in ("warehouse", "branch_manager", "prorab"):
            with self.subTest(role=role):
                self.auth(self.users[role])
                response = self.client.get(reverse("document-detail", args=[self.document_b.id]))
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
        # Omborchi — filialga bog'langan rol. Markaziy rollar bu yerda
        # ishlatilmaydi: ular barcha filiallarni ataylab ko'radi
        # (test_global_roles_see_every_branch).
        self.auth(self.users["warehouse"])  # A filiali
        response = self.client.get(reverse("document-detail", args=[self.document_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_upload_to_another_branch_document_is_blocked(self):
        self.auth(self.users["warehouse"])  # A filiali
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
            ("branch_manager", "submit", "architecture"),
            ("architecture", "approve", "ceo"),
            ("ceo", "approve", "procurement"),
            ("procurement", "approve", "anticorruption"),
            ("anticorruption", "approve", "accountant"),
            ("accountant", "approve", "delivering"),
            ("warehouse", "advance", "received"),
            ("warehouse", "close", "closed"),
        ]

        for role, action, expected_status in chain:
            with self.subTest(role=role, action=action):
                self.auth(self.users[role])
                response = self.client.post(url, {"action": action}, format="json")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["status"], expected_status)

    def test_the_chain_completes_across_branches(self):
        """
        Zanjir boshqa filial hujjatida ham oxirigacha boradi.

        Ilgari `architecture` va `accountant` filialga bog'langan edi, lekin
        ikkalasi ham zanjir bosqichi: begona filial hujjati ularga umuman
        ko'rinmasdi va `approve` 403 emas, **404** qaytarardi — ya'ni filialda
        o'z arxitektori bo'lmasa so'rov birinchi tasdiqdayoq o'lib qolardi.

        Omborchi bu yerda B filialiniki: u tovarni jismonan qabul qiladi va
        ataylab filialga bog'langan bo'lib qoladi.
        """
        document = self._create_document("XR-2026-0150", branch=self.branch_b)
        url = reverse("document-workflow", args=[document.id])

        chain = [
            (self.users["procurement"], "submit", "architecture"),
            (self.users["architecture"], "approve", "ceo"),
            (self.users["ceo"], "approve", "procurement"),
            (self.users["procurement"], "approve", "anticorruption"),
            (self.users["anticorruption"], "approve", "accountant"),
            (self.users["accountant"], "approve", "delivering"),
            (self.warehouse_user_b, "advance", "received"),
            (self.warehouse_user_b, "close", "closed"),
        ]

        for user, action, expected_status in chain:
            with self.subTest(user=user.email, action=action):
                self.auth(user)
                response = self.client.post(url, {"action": action}, format="json")

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                    f"{user.email} «{action}» ni bajara olmadi: {response.data}",
                )
                self.assertEqual(response.data["status"], expected_status)

    def test_warehouse_stays_branch_bound(self):
        """
        Omborchi begona filial hujjatini qabul qila olmaydi — tovar jismonan
        uning omboriga kelmaydi.
        """
        document = self._create_document("XR-2026-0151", branch=self.branch_b)
        document.status = "delivering"
        document.save(update_fields=["status"])

        self.auth(self.users["warehouse"])  # A filiali
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "advance"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_each_stage_rejects_the_wrong_role(self):
        """Zanjirning har bosqichida faqat mas'ul rol o'ta oladi."""
        # (bosqich, o'sha bosqichga tegishli BO'LMAGAN rol)
        cases = [
            ("architecture", "accountant"),
            ("ceo", "procurement"),
            ("procurement", "accountant"),
            ("anticorruption", "procurement"),
            ("accountant", "anticorruption"),
        ]

        for index, (stage, wrong_role) in enumerate(cases):
            with self.subTest(stage=stage, role=wrong_role):
                document = self._create_document(f"XR-2026-02{index:02d}")
                document.status = stage
                document.save(update_fields=["status"])

                self.auth(self.users[wrong_role])
                response = self.client.post(
                    reverse("document-workflow", args=[document.id]),
                    {"action": "approve"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anticorruption_stage_cannot_be_skipped(self):
        """Xaridlardan keyin hujjat to'g'ridan-to'g'ri buxgalteriyaga o'tmaydi."""
        document = self._create_document("XR-2026-0210")
        document.status = "procurement"
        document.save(update_fields=["status"])

        self.auth(self.users["procurement"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "approve"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "anticorruption")

    def test_anticorruption_can_reject_before_payment(self):
        document = self._create_document("XR-2026-0211")
        document.status = "anticorruption"
        document.save(update_fields=["status"])

        self.auth(self.users["anticorruption"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]),
            {"action": "reject", "comment": "Ombor qoldig'i yetarli."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejected")

    def test_branch_manager_can_submit_own_request(self):
        """Yangi oqim filial rahbaridan boshlanadi — u so'rovni o'zi jo'natadi."""
        document = self._create_document("XR-2026-0212")

        self.auth(self.users["branch_manager"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "submit"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "architecture")

    def test_allowed_actions_match_the_server_rules(self):
        """
        `allowed_actions` va haqiqiy tekshiruv bitta manbadan o'qiladi.
        Ular ajralib qolsa foydalanuvchiga bosilganda 403 beradigan tugma
        ko'rinadi — shuning uchun ikkalasi solishtiriladi.
        """
        document = self._create_document("XR-2026-0213")
        document.status = "anticorruption"
        document.save(update_fields=["status"])
        url = reverse("document-detail", args=[document.id])

        self.auth(self.users["anticorruption"])
        self.assertEqual(
            sorted(self.client.get(url).data["allowed_actions"]),
            ["approve", "reject", "return"],
        )

        self.auth(self.users["accountant"])
        self.assertEqual(self.client.get(url).data["allowed_actions"], [])

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


class DocumentManagementRoleTests(BaseAPITestCase):
    """
    Xaridlar bo'limi begona hujjatni o'zi tahrirlamaydi va o'chirmaydi —
    kamchilikni ko'rsa filial rahbariga aytadi, tuzatishni u kiritadi.
    Xaridlarning ta'siri zanjirdagi o'z bosqichida qoladi.
    """

    def _create_document(self, doc_number="XR-2026-0800", doc_status="created"):
        return Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Filial rahbari so'rovi",
            created_by=self.users["branch_manager"],
            branch=self.branch_a,
            status=doc_status,
        )

    def test_procurement_cannot_edit_someone_elses_document(self):
        document = self._create_document("XR-2026-0801")

        self.auth(self.users["procurement"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "Xaridlar tuzatdi"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        document.refresh_from_db()
        self.assertEqual(document.title, "Filial rahbari so'rovi")

    def test_procurement_cannot_delete_someone_elses_document(self):
        document = self._create_document("XR-2026-0802")

        self.auth(self.users["procurement"])
        response = self.client.delete(reverse("document-detail", args=[document.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Document.objects.filter(id=document.id).exists())

    def test_procurement_still_manages_its_own_document(self):
        """Muallif cheklovi o'z kuchida — o'zi yaratganini tahrirlaydi."""
        document = self._create_document("XR-2026-0803")
        document.created_by = self.users["procurement"]
        document.save(update_fields=["created_by"])

        self.auth(self.users["procurement"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "O'z hujjati"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_branch_manager_manages_branch_documents(self):
        document = Document.objects.create(
            doc_number="XR-2026-0804",
            doc_type="purchase_request",
            title="Prorab so'rovi",
            created_by=self.users["prorab"],
            branch=self.branch_a,
        )

        self.auth(self.users["branch_manager"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"title": "Rahbar tuzatdi"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_procurement_keeps_its_workflow_stage(self):
        """Tahrirlash huquqi olingani zanjirdagi qarorga tegmaydi."""
        document = self._create_document("XR-2026-0805", "procurement")

        self.auth(self.users["procurement"])
        response = self.client.post(
            reverse("document-workflow", args=[document.id]), {"action": "approve"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "anticorruption")


class DocumentCommentTests(BaseAPITestCase):
    """
    Hujjatga bog'langan yozishma.

    Ilgari fikr bildirishning yagona yo'li `DocumentApproval.comment` edi va u
    faqat holat o'zgarganda yozilardi — ya'ni xaridlar bo'limi kamchilikni
    ko'rsa ham (tuzatishni endi faqat filial rahbari kiritadi) aytadigan joyi
    yo'q edi.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.document = Document.objects.create(
            doc_number="XR-2026-0900",
            doc_type="purchase_request",
            title="Izoh testi",
            created_by=cls.users["branch_manager"],
            branch=cls.branch_a,
        )
        cls.document_b = Document.objects.create(
            doc_number="XR-2026-0901",
            doc_type="purchase_request",
            title="B filiali hujjati",
            created_by=cls.warehouse_user_b,
            branch=cls.branch_b,
        )

    def _url(self, document=None):
        return reverse("document-comment-list", args=[(document or self.document).id])

    def _post(self, text, document=None):
        return self.client.post(self._url(document), {"text": text}, format="json")

    def test_comment_is_written_and_listed(self):
        self.auth(self.users["procurement"])
        created = self._post("Miqdor ombor qoldig'idan ko'p ko'rinadi.")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["author"], self.users["procurement"].id)

        listed = self.client.get(self._url())
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(listed.data["results"][0]["text"], "Miqdor ombor qoldig'idan ko'p ko'rinadi.")

    def test_comments_are_listed_in_chronological_order(self):
        """Yozishma xronologik o'qiladi — boshqa ro'yxatlardan farqli o'laroq."""
        self.auth(self.users["procurement"])
        self._post("Birinchi")
        self._post("Ikkinchi")

        texts = [item["text"] for item in self.client.get(self._url()).data["results"]]
        self.assertEqual(texts, ["Birinchi", "Ikkinchi"])

    def test_frozen_document_still_accepts_comments(self):
        """
        Muzlatish izohga tegishli emas: aynan muzlagan hujjat haqida
        gaplashish kerak bo'ladi.
        """
        for doc_status in ("architecture", "ceo", "anticorruption", "closed"):
            with self.subTest(status=doc_status):
                self.document.status = doc_status
                self.document.save(update_fields=["status"])

                self.auth(self.users["procurement"])
                response = self._post(f"{doc_status} bosqichidagi izoh")
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_control_role_can_comment(self):
        """
        Kuzatuvini qayd eta olmaydigan nazoratning ma'nosi qolmaydi. Bu SoD ni
        buzmaydi — izoh qaror emas va hujjat mazmunini o'zgartirmaydi.
        """
        self.auth(self.users["anticorruption"])
        response = self._post("Ta'minotchi narxi bozor narxidan yuqori.")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], self.users["anticorruption"].id)

    def test_comment_cannot_be_edited_or_deleted(self):
        """
        Yozishma tarixi keyin o'zgartirilsa dalil sifatidagi qiymati qolmaydi —
        shuning uchun tafsilot endpointi umuman yo'q.
        """
        self.auth(self.users["procurement"])
        self._post("O'zgarmaydigan izoh")

        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self._url())
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(DocumentComment.objects.count(), 1)

    def test_empty_comment_is_rejected(self):
        self.auth(self.users["procurement"])
        response = self._post("   ")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DocumentComment.objects.count(), 0)

    def test_author_comes_from_the_token_not_the_payload(self):
        self.auth(self.users["prorab"])
        response = self.client.post(
            self._url(),
            {"text": "Boshqa nomdan", "author": self.users["ceo"].id, "document": self.document_b.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = DocumentComment.objects.get()
        self.assertEqual(comment.author_id, self.users["prorab"].id)
        self.assertEqual(comment.document_id, self.document.id)

    def test_comments_of_another_branch_are_hidden(self):
        DocumentComment.objects.create(
            document=self.document_b, author=self.warehouse_user_b, text="B filiali izohi"
        )

        self.auth(self.users["warehouse"])  # A filiali, markaziy rol emas
        self.assertEqual(self.client.get(self._url(self.document_b)).data["count"], 0)

    def test_comment_on_another_branch_document_is_blocked(self):
        self.auth(self.users["warehouse"])  # A filiali, markaziy rol emas
        response = self._post("Begona filialga izoh", self.document_b)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(DocumentComment.objects.count(), 0)

    def test_comment_notifies_the_document_author(self):
        self.auth(self.users["procurement"])
        self._post("Tuzatish kerak")

        self.assertTrue(
            Notification.objects.filter(user=self.users["branch_manager"]).exists(),
            "Filial rahbari izohdan xabardor bo'lishi kerak",
        )


class DocumentReturnTests(BaseAPITestCase):
    """
    Tuzatishga qaytarish (`return`) — `reject` ning yumshoq muqobili.

    Ilgari oraliq bosqichdagi mayda xatoni tuzatishning yagona yo'li hujjatni
    butunlay rad etish edi. Farq mahsulot ma'nosida: "rad etildi" emas,
    "tuzatib qayta yuboring".
    """

    STAGE_ROLES = [
        ("architecture", "architecture"),
        ("ceo", "ceo"),
        ("procurement", "procurement"),
        ("anticorruption", "anticorruption"),
        ("accountant", "accountant"),
    ]

    def _create_document(self, doc_number, doc_status="created"):
        return Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Qaytarish testi",
            created_by=self.users["branch_manager"],
            branch=self.branch_a,
            status=doc_status,
            total_amount=Decimal("1000.00"),
        )

    def _act(self, document, payload):
        return self.client.post(
            reverse("document-workflow", args=[document.id]), payload, format="json"
        )

    def test_every_approval_stage_can_return(self):
        for index, (stage, role) in enumerate(self.STAGE_ROLES):
            with self.subTest(stage=stage):
                document = self._create_document(f"XR-2026-10{index:02d}", stage)

                self.auth(self.users[role])
                response = self._act(document, {"action": "return", "comment": "Miqdorni tekshiring"})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["status"], "revision")

    def test_return_requires_a_comment(self):
        """Nima tuzatilishi kerakligini aytmasdan qaytarish — boshi berk ko'cha."""
        document = self._create_document("XR-2026-1010", "ceo")

        self.auth(self.users["ceo"])
        response = self._act(document, {"action": "return"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        document.refresh_from_db()
        self.assertEqual(document.status, "ceo")

    def test_wrong_role_cannot_return(self):
        document = self._create_document("XR-2026-1011", "ceo")

        self.auth(self.users["accountant"])
        response = self._act(document, {"action": "return", "comment": "Tuzating"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_execution_stages_have_no_return(self):
        """
        `delivering` va `received` da qaytarish yo'q — `reject` qanday sababga
        ko'ra yo'q bo'lsa, `return` ham shu sababga ko'ra yo'q: tovar yo'lga
        chiqqach hujjatni orqaga surish qoldiqni holatdan ajratib yuborardi.
        """
        for index, stage in enumerate(("delivering", "received", "closed")):
            with self.subTest(stage=stage):
                document = self._create_document(f"XR-2026-102{index}", stage)

                self.auth(self.users["admin"])
                response = self._act(document, {"action": "return", "comment": "Tuzating"})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returned_document_becomes_editable(self):
        """Qaytarishning butun ma'nosi shu — hujjat muzlashdan chiqadi."""
        document = self._create_document("XR-2026-1030", "procurement")

        self.auth(self.users["procurement"])
        self._act(document, {"action": "return", "comment": "Summa noto'g'ri"})

        self.auth(self.users["branch_manager"])
        response = self.client.patch(
            reverse("document-detail", args=[document.id]), {"total_amount": "2000.00"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        document.refresh_from_db()
        self.assertEqual(document.total_amount, Decimal("2000.00"))

    def test_resubmit_starts_the_chain_from_architecture(self):
        """
        Zanjir qaytadan boshlanadi — ataylab. Summa yoki qatorlar o'zgargan
        bo'lsa oldingi tasdiqlar boshqa hujjatga tegishli bo'lib qoladi.
        """
        document = self._create_document("XR-2026-1031", "revision")

        self.auth(self.users["branch_manager"])
        response = self._act(document, {"action": "submit"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "architecture")

    def test_the_returning_user_is_notified_on_resubmit(self):
        document = self._create_document("XR-2026-1032", "accountant")

        self.auth(self.users["accountant"])
        self._act(document, {"action": "return", "comment": "Hisob-faktura yo'q"})
        Notification.objects.all().delete()

        self.auth(self.users["branch_manager"])
        self._act(document, {"action": "submit"})

        self.assertTrue(
            Notification.objects.filter(
                user=self.users["accountant"], title="Qaytarilgan hujjat qayta yuborildi"
            ).exists(),
            "Qaytargan foydalanuvchi qayta yuborilganidan xabardor bo'lishi kerak",
        )

    def test_return_leaves_a_trail_with_the_reason(self):
        document = self._create_document("XR-2026-1033", "architecture")

        self.auth(self.users["architecture"])
        response = self._act(document, {"action": "return", "comment": "Obyekt ko'rsatilmagan"})

        approval = response.data["approvals"][0]
        self.assertEqual(approval["action"], "return")
        self.assertEqual(approval["comment"], "Obyekt ko'rsatilmagan")

    def test_control_role_can_return_at_its_own_stage(self):
        """Nazoratning zanjirdagi istisnosi yangi amalga ham tegishli."""
        document = self._create_document("XR-2026-1040", "anticorruption")

        self.auth(self.users["anticorruption"])
        response = self._act(document, {"action": "return", "comment": "Narx asoslanmagan"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "revision")


class DocumentReceiptTests(BaseAPITestCase):
    """
    Qabul (`delivering → received`) ombor qoldig'ini oshiradi.

    Ilgari bu o'tish faqat statusni almashtirardi: zanjir yakunlangan, tovar
    omborda, lekin qoldiq eski. Ya'ni xaridlar bo'limi keyingi so'rov bo'yicha
    qaror qabul qilishda ko'radigan raqam zanjir natijasini aks ettirmasdi.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.supplier = Supplier.objects.create(name="Ta'minotchi", code="SUP-RC")
        cls.material = Material.objects.create(name="Sement", code="MAT-RC", unit="qop")
        cls.warehouse_a = Warehouse.objects.create(name="A ombori", code="WH-RC-A", branch=cls.branch_a)
        cls.warehouse_b = Warehouse.objects.create(name="B ombori", code="WH-RC-B", branch=cls.branch_b)

    def _delivering_document(self, doc_number, quantity=Decimal("10.000"), with_items=True):
        document = Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Qabul testi",
            created_by=self.users["branch_manager"],
            branch=self.branch_a,
            status="delivering",
            total_amount=Decimal("1000.00"),
        )
        if with_items:
            purchase_order = PurchaseOrder.objects.create(document=document, supplier=self.supplier)
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                material=self.material,
                quantity=quantity,
                unit_price=Decimal("100.00"),
                total_price=quantity * Decimal("100.00"),
            )
        return document

    def _advance(self, document, warehouse=None, **extra):
        payload = {"action": "advance", **extra}
        if warehouse is not None:
            payload["warehouse"] = warehouse.id
        return self.client.post(
            reverse("document-workflow", args=[document.id]), payload, format="json"
        )

    def test_receipt_increases_the_stock(self):
        document = self._delivering_document("XR-2026-1100")

        self.auth(self.users["warehouse"])
        response = self._advance(document, self.warehouse_a)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "received")
        item = InventoryItem.objects.get(warehouse=self.warehouse_a, material=self.material)
        self.assertEqual(item.quantity, Decimal("10.000"))

    def test_receipt_adds_to_an_existing_balance(self):
        InventoryItem.objects.create(
            warehouse=self.warehouse_a, material=self.material, quantity=Decimal("5.000")
        )
        document = self._delivering_document("XR-2026-1101")

        self.auth(self.users["warehouse"])
        self._advance(document, self.warehouse_a)

        item = InventoryItem.objects.get(warehouse=self.warehouse_a, material=self.material)
        self.assertEqual(item.quantity, Decimal("15.000"))

    def test_receipt_records_a_movement_linked_to_the_document(self):
        """Kirim tarixda hujjatga bog'langan holda qoladi — tekshirib bo'ladi."""
        document = self._delivering_document("XR-2026-1102")

        self.auth(self.users["warehouse"])
        self._advance(document, self.warehouse_a)

        movement = StockMovement.objects.get(reference_doc=document)
        self.assertEqual(movement.movement_type, "IN")
        self.assertEqual(movement.quantity, Decimal("10.000"))
        self.assertEqual(movement.warehouse_id, self.warehouse_a.id)
        self.assertEqual(movement.performed_by_id, self.users["warehouse"].id)

    def test_the_warehouse_is_never_guessed(self):
        """
        Filialda bitta ombor bo'lsa ham taxmin qilinmaydi: tovarni qabul
        qilayotgan omborchi u qayerga kirganini o'zi ko'rsatadi, va noto'g'ri
        kirim keyin faqat teskari harakat bilan tuzatiladi.
        """
        self.assertEqual(Warehouse.objects.filter(branch=self.branch_a).count(), 1)
        document = self._delivering_document("XR-2026-1105")

        self.auth(self.users["warehouse"])
        response = self._advance(document)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        document.refresh_from_db()
        self.assertEqual(document.status, "delivering")

    def test_the_chosen_warehouse_receives_the_items(self):
        second = Warehouse.objects.create(name="A-2 ombori", code="WH-RC-A2", branch=self.branch_a)
        document = self._delivering_document("XR-2026-1106")

        self.auth(self.users["warehouse"])
        response = self._advance(document, second)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            InventoryItem.objects.get(warehouse=second, material=self.material).quantity,
            Decimal("10.000"),
        )
        self.assertFalse(InventoryItem.objects.filter(warehouse=self.warehouse_a).exists())

    def test_document_without_items_is_received_without_a_warehouse(self):
        """
        Xarid buyurtmasi yo'q yoki qatorlari bo'sh — kirim qiladigan narsa
        yo'q, ya'ni ombor ham so'ralmaydi. Bu xato emas.
        """
        document = self._delivering_document("XR-2026-1103", with_items=False)

        self.auth(self.users["warehouse"])
        response = self._advance(document)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "received")
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_empty_purchase_order_is_received_without_a_warehouse(self):
        document = self._delivering_document("XR-2026-1108", with_items=False)
        PurchaseOrder.objects.create(document=document, supplier=self.supplier)

        self.auth(self.users["warehouse"])
        response = self._advance(document)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "received")
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_warehouse_of_another_branch_is_rejected(self):
        document = self._delivering_document("XR-2026-1104")

        self.auth(self.users["warehouse"])
        response = self._advance(document, self.warehouse_b)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        document.refresh_from_db()
        self.assertEqual(document.status, "delivering")

    def test_a_failed_receipt_leaves_nothing_behind(self):
        """Kirim va status bitta transaksiyada — yarim bajarilgan qabul yo'q."""
        document = self._delivering_document("XR-2026-1107")

        self.auth(self.users["warehouse"])
        response = self._advance(document, self.warehouse_b)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        document.refresh_from_db()
        self.assertEqual(document.status, "delivering")
        self.assertEqual(document.approvals.count(), 0)
        self.assertEqual(StockMovement.objects.count(), 0)
        self.assertEqual(InventoryItem.objects.count(), 0)

    def test_receipt_is_still_limited_to_the_warehouse_role(self):
        """Qoldiqni o'zgartiradigan amal — rol tekshiruvi joyida qoladi."""
        document = self._delivering_document("XR-2026-1109")

        self.auth(self.users["accountant"])
        response = self._advance(document, self.warehouse_a)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(StockMovement.objects.count(), 0)


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
