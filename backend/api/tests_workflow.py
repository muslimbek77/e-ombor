"""
Tasdiqlash zanjiri: bosqichlar, rol tekshiruvi, tuzatishga qaytarish,
ombor qabuli va hujjatni boshqarish huquqi.
"""

from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import (
    Document,
    InventoryItem,
    Material,
    Notification,
    PurchaseOrder,
    PurchaseOrderItem,
    StockMovement,
    Supplier,
    Warehouse,
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
