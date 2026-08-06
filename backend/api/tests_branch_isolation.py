"""
Filial izolyatsiyasi — tizimning eng muhim qoidasi.

Markaziy rollar barcha filialni ko'radi (qaror qabul qilish yoki zanjir
bosqichi bo'lgani uchun); qolganlar faqat o'zinikini.
"""

from __future__ import annotations


from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import ConstructionSite, Document, Warehouse


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
