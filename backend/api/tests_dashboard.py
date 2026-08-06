"""Dashboard agregatsiyasi — zanjirdan hosil bo'lgan ro'yxatlar eskirmasligi."""

from __future__ import annotations

from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import Document


class PendingApprovalsTests(BaseAPITestCase):
    """
    `pending_approvals` ilgari qo'lda ["architecture", "ceo"] deb sanalgan
    edi — zanjir qayta qurilgach `procurement`, `anticorruption`,
    `accountant` va `revision` hisobga olinmay qoldi.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        def make(doc_status, number):
            return Document.objects.create(
                doc_number=number,
                doc_type="purchase_request",
                title=f"Hujjat {number}",
                created_by=cls.users["branch_manager"],
                branch=cls.branch_a,
                status=doc_status,
            )

        cls.counted_statuses = ["architecture", "ceo", "procurement", "anticorruption", "accountant", "revision"]
        cls.excluded_statuses = ["created", "delivering", "received", "rejected", "closed"]
        for index, doc_status in enumerate(cls.counted_statuses + cls.excluded_statuses):
            make(doc_status, f"XR-2026-08{index:02d}")

    def test_pending_approvals_counts_every_decision_stage_and_revision(self):
        self.auth(self.users["admin"])
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending_approvals"], len(self.counted_statuses))
