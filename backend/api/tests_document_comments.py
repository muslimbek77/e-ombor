"""Hujjatga bog'langan yozishma."""

from __future__ import annotations


from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import Document, DocumentComment, Notification


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
