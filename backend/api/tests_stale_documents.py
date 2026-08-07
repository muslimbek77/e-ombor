"""Uzoq vaqt bir holatda qolgan hujjatlar uchun eslatma buyrug'i."""

from __future__ import annotations

from io import StringIO

from django.core.management import call_command
from django.utils import timezone

from .tests_base import BaseAPITestCase

from .models import Document, Notification


class EscalateStaleDocumentsTests(BaseAPITestCase):
    """`escalate_stale_documents` mas'ul rollarga eslatma yuboradi."""

    def _create_document(self, status, updated_at, doc_number="XR-2026-0200"):
        document = Document.objects.create(
            doc_number=doc_number,
            doc_type="purchase_request",
            title="Eskirgan hujjat",
            created_by=self.users["prorab"],
            branch=self.branch_a,
            status=status,
        )
        Document.objects.filter(pk=document.pk).update(updated_at=updated_at)
        return document

    def test_stale_document_notifies_responsible_roles(self):
        document = self._create_document(
            "delivering", timezone.now() - timezone.timedelta(days=5)
        )

        call_command("escalate_stale_documents", stdout=StringIO())

        self.assertTrue(
            Notification.objects.filter(
                user=self.users["warehouse"], title="Hujjat uzoq vaqt kutmoqda"
            ).exists()
        )
        self.assertIn(
            document.doc_number,
            Notification.objects.get(
                user=self.users["warehouse"], title="Hujjat uzoq vaqt kutmoqda"
            ).message,
        )

    def test_fresh_document_is_not_escalated(self):
        self._create_document(
            "architecture", timezone.now(), doc_number="XR-2026-0201"
        )

        call_command("escalate_stale_documents", stdout=StringIO())

        self.assertFalse(
            Notification.objects.filter(title="Hujjat uzoq vaqt kutmoqda").exists()
        )

    def test_editable_status_is_never_escalated(self):
        self._create_document(
            "created", timezone.now() - timezone.timedelta(days=30), doc_number="XR-2026-0202"
        )

        call_command("escalate_stale_documents", stdout=StringIO())

        self.assertFalse(
            Notification.objects.filter(title="Hujjat uzoq vaqt kutmoqda").exists()
        )
