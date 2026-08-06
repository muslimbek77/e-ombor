"""Autentifikatsiya oqimi va foydalanuvchi boshqaruvi."""

from __future__ import annotations


from django.urls import reverse
from rest_framework import status

from .tests_base import ROLE_KEYS, BaseAPITestCase, User


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
