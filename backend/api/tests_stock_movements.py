from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from api.models import Branch, Document, InventoryItem, Material, StockMovement, User, Warehouse


class StockMovementBranchScopeTests(APITestCase):
    """Filial cheklovi: warehouse roli faqat o'z filiali omborlari bilan ishlaydi, admin cheklanmagan."""

    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Markaz", code="MRK")
        cls.other_branch = Branch.objects.create(name="Fargona", code="FRG")
        cls.wh1 = Warehouse.objects.create(name="Ombor 1", code="W1", branch=cls.branch)
        cls.wh2 = Warehouse.objects.create(name="Ombor 2", code="W2", branch=cls.branch)
        cls.wh_other = Warehouse.objects.create(name="Ombor 3", code="W3", branch=cls.other_branch)
        cls.material = Material.objects.create(name="Sement", code="M1")
        cls.keeper = User.objects.create_user(
            email="w@t.uz", password="Pass12345!", roles=["warehouse"], branch=cls.branch
        )
        cls.keeper_no_branch = User.objects.create_user(
            email="wnb@t.uz", password="Pass12345!", roles=["warehouse"]
        )
        cls.admin = User.objects.create_user(
            email="a@t.uz", password="Pass12345!", roles=["admin"], is_staff=True
        )

    def setUp(self):
        self.url = reverse("stock-movement-list")

    def qty(self, warehouse):
        item = InventoryItem.objects.filter(warehouse=warehouse, material=self.material).first()
        return item.quantity if item else None

    def post(self, user, payload):
        self.client.force_authenticate(user)
        return self.client.post(self.url, payload, format="json")

    def test_keeper_own_branch_ok(self):
        r = self.post(self.keeper, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "5",
        })
        self.assertEqual(r.status_code, 201, r.data)

    def test_keeper_foreign_source_forbidden(self):
        r = self.post(self.keeper, {
            "warehouse": self.wh_other.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "1",
        })
        self.assertEqual(r.status_code, 403)

    def test_keeper_transfer_within_own_branch_ok(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("9"))
        r = self.post(self.keeper, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "4",
        })
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.qty(self.wh1), Decimal("5.000"))
        self.assertEqual(self.qty(self.wh2), Decimal("4.000"))

    def test_keeper_transfer_to_foreign_target_forbidden(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("9"))
        r = self.post(self.keeper, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh_other.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "4",
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.qty(self.wh1), Decimal("9.000"))
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_keeper_transfer_from_foreign_source_forbidden(self):
        InventoryItem.objects.create(warehouse=self.wh_other, material=self.material, quantity=Decimal("9"))
        r = self.post(self.keeper, {
            "warehouse": self.wh_other.id, "target_warehouse": self.wh1.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "4",
        })
        self.assertEqual(r.status_code, 403)

    def test_branchless_keeper_forbidden_everywhere(self):
        for wh in (self.wh1, self.wh_other):
            r = self.post(self.keeper_no_branch, {
                "warehouse": wh.id, "material": self.material.id,
                "movement_type": "IN", "quantity": "1",
            })
            self.assertEqual(r.status_code, 403, wh.code)

    def test_admin_cross_branch_transfer_ok(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("5"))
        r = self.post(self.admin, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh_other.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "5",
        })
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.qty(self.wh1), Decimal("0.000"))
        self.assertEqual(self.qty(self.wh_other), Decimal("5.000"))

    def test_admin_any_branch_in_ok(self):
        r = self.post(self.admin, {
            "warehouse": self.wh_other.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "3",
        })
        self.assertEqual(r.status_code, 201, r.data)


class StockMovementCreateTests(APITestCase):
    """IN/OUT/TRANSFER mantiqi va qoldiqning avtomatik yangilanishi."""

    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Markaz", code="MRK")
        cls.wh1 = Warehouse.objects.create(name="Ombor 1", code="W1", branch=cls.branch)
        cls.wh2 = Warehouse.objects.create(name="Ombor 2", code="W2", branch=cls.branch)
        cls.material = Material.objects.create(name="Sement", code="M1")
        cls.keeper = User.objects.create_user(
            email="w@t.uz", password="Pass12345!", roles=["warehouse"], branch=cls.branch
        )
        cls.prorab = User.objects.create_user(
            email="p@t.uz", password="Pass12345!", roles=["prorab"], branch=cls.branch
        )

    def setUp(self):
        self.url = reverse("stock-movement-list")
        self.client.force_authenticate(self.keeper)

    def qty(self, warehouse):
        item = InventoryItem.objects.filter(warehouse=warehouse, material=self.material).first()
        return item.quantity if item else None

    def test_in_creates_missing_inventory_item(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "10.5",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.qty(self.wh1), Decimal("10.500"))
        self.assertEqual(r.data["performed_by"], self.keeper.id)
        self.assertIsNotNone(r.data["performed_at"])

    def test_in_increments_existing(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("5"))
        self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "3",
        }, format="json")
        self.assertEqual(self.qty(self.wh1), Decimal("8.000"))

    def test_out_decrements(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("5"))
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "OUT", "quantity": "2",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.qty(self.wh1), Decimal("3.000"))

    def test_out_insufficient_rolls_back(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("1"))
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "OUT", "quantity": "5",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.qty(self.wh1), Decimal("1.000"))
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_out_with_no_inventory_row(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "OUT", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_transfer_moves_stock(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("10"))
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "4",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(self.qty(self.wh1), Decimal("6.000"))
        self.assertEqual(self.qty(self.wh2), Decimal("4.000"))
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_transfer_insufficient_rolls_back_both_sides(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("2"))
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "5",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.qty(self.wh1), Decimal("2.000"))
        self.assertIsNone(self.qty(self.wh2))
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_transfer_from_empty_source(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_transfer_requires_target(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "TRANSFER", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("target_warehouse", r.data)

    def test_transfer_target_must_differ(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh1.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 400)

    def test_target_rejected_for_non_transfer(self):
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "IN", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 400)

    def test_quantity_must_be_positive(self):
        for bad in ("0", "-3"):
            r = self.client.post(self.url, {
                "warehouse": self.wh1.id, "material": self.material.id,
                "movement_type": "IN", "quantity": bad,
            }, format="json")
            self.assertEqual(r.status_code, 400, bad)

    def test_role_forbidden(self):
        self.client.force_authenticate(self.prorab)
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 403)

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "1",
        }, format="json")
        self.assertEqual(r.status_code, 401)

    def test_list_shows_transfer_on_both_warehouse_filters(self):
        InventoryItem.objects.create(warehouse=self.wh1, material=self.material, quantity=Decimal("5"))
        self.client.post(self.url, {
            "warehouse": self.wh1.id, "target_warehouse": self.wh2.id,
            "material": self.material.id, "movement_type": "TRANSFER", "quantity": "1",
        }, format="json")
        for wh in (self.wh1, self.wh2):
            r = self.client.get(self.url, {"warehouse": wh.id})
            results = r.data["results"] if isinstance(r.data, dict) and "results" in r.data else r.data
            self.assertEqual(len(results), 1, f"warehouse={wh.code}")

    def test_reference_doc_optional_and_stored(self):
        doc = Document.objects.create(
            doc_number="XR-2026-0001", doc_type="purchase_request",
            title="Test", created_by=self.keeper, branch=self.branch,
        )
        r = self.client.post(self.url, {
            "warehouse": self.wh1.id, "material": self.material.id,
            "movement_type": "IN", "quantity": "1", "reference_doc": doc.id,
            "notes": "hujjat asosida",
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["reference_doc"], doc.id)
        self.assertEqual(r.data["notes"], "hujjat asosida")
