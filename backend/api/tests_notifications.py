"""Bildirishnomalar faqat egasiga ko'rinadi."""

from __future__ import annotations


from django.urls import reverse
from rest_framework import status

from .tests_base import BaseAPITestCase

from .models import Notification


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
