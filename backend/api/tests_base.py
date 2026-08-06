"""
Test to'plamlari uchun umumiy tayyorgarlik.

Bitta `tests_api_contract.py` (2000 qator) o'rniga bir necha `tests_*.py` —
Django ularni o'zi topadi. Bo'lish tekshiruvlarni o'zgartirmadi: har bir
test o'z faylida, ammo bazasi shu yerda.

Testlar to'g'ri (kutilgan) xulqni tasdiqlaydi. Yiqilgan test — tuzatilishi
kerak bo'lgan xato, testni moslashtirish emas.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Branch


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
