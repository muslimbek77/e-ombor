from __future__ import annotations

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import (
    Address,
    AuditLog,
    Branch,
    ConstructionSite,
    Contract,
    Document,
    DocumentApproval,
    DocumentFile,
    InventoryItem,
    Invoice,
    Material,
    Notification,
    Payment,
    ProductionRequest,
    PurchaseOrder,
    PurchaseOrderItem,
    StockMovement,
    Supplier,
    Ticket,
    Warehouse,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Barcha modellar uchun demo/fake ma'lumotlarni yaratadi."

    def handle(self, *args, **options):
        with transaction.atomic():
            payload = self.seed_demo_data()

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar tayyorlandi."))
        self.stdout.write("")
        self.stdout.write("Demo loginlar:")
        for item in payload["credentials"]:
            self.stdout.write(
                f"- {item['email']} | {item['password']} | {item['roles']} | {item['full_name']}"
            )

    def seed_demo_data(self):
        branches = self._seed_branches()
        users = self._seed_users(branches)
        sites = self._seed_sites(branches, users)
        warehouses = self._seed_warehouses(branches)
        materials = self._seed_materials()
        suppliers = self._seed_suppliers()
        addresses = self._seed_addresses()
        documents = self._seed_documents(branches, sites, users)
        self._seed_document_approvals(documents, users)
        self._seed_purchase_orders(documents, suppliers, materials)
        contracts = self._seed_contracts(documents, suppliers)
        invoices = self._seed_invoices(documents, contracts)
        self._seed_payments(invoices, users)
        self._seed_inventory(warehouses, materials)
        self._seed_stock_movements(warehouses, materials, users)
        self._seed_document_files(documents, users)
        self._seed_production_requests(sites, users)
        self._seed_tickets(branches, sites, users)
        self._seed_notifications(users)
        self._seed_audit_logs(users, documents, suppliers, sites, warehouses)

        return {
            "branches": branches,
            "users": users,
            "sites": sites,
            "warehouses": warehouses,
            "materials": materials,
            "suppliers": suppliers,
            "addresses": addresses,
            "documents": documents,
            "contracts": contracts,
            "invoices": invoices,
            "credentials": [
                {
                    "email": user.email,
                    "password": self.demo_passwords[user.email],
                    "roles": ", ".join(user.roles or []),
                    "full_name": user.full_name,
                }
                for user in users
            ],
        }

    def _seed_branches(self):
        branch_specs = [
            {
                "code": "BR-001",
                "name": "Toshkent Bosh Filiali",
                "address": "Toshkent sh., Yunusobod tumani, Amir Temur ko'chasi 108",
                "phone": "+998712000001",
            },
            {
                "code": "BR-002",
                "name": "Samarqand Filiali",
                "address": "Samarqand sh., Universitet xiyoboni 12",
                "phone": "+998662000002",
            },
            {
                "code": "BR-003",
                "name": "Farg'ona Filiali",
                "address": "Farg'ona sh., Mustaqillik ko'chasi 25",
                "phone": "+998732000003",
            },
        ]
        branches = []
        for spec in branch_specs:
            branch, _ = Branch.objects.get_or_create(code=spec["code"], defaults=spec)
            branches.append(branch)
        return branches

    def _seed_users(self, branches):
        branch_main, branch_secondary, branch_third = branches
        user_specs = [
            {
                "email": "admin@eombor.uz",
                "password": "Admin123!",
                "first_name": "Admin",
                "last_name": "E-Ombor",
                "phone": "+998901111111",
                "stir_inn": "123456789012",
                "roles": ["admin"],
                "branch": branch_main,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "ceo@eombor.uz",
                "password": "Ceo12345!",
                "first_name": "Dilshod",
                "last_name": "Karimov",
                "phone": "+998901111112",
                "stir_inn": "123456789013",
                "roles": ["ceo"],
                "branch": branch_main,
            },
            {
                "email": "procurement@eombor.uz",
                "password": "Procure123!",
                "first_name": "Malika",
                "last_name": "Ismoilova",
                "phone": "+998901111113",
                "stir_inn": "123456789014",
                "roles": ["procurement"],
                "branch": branch_main,
            },
            {
                "email": "accountant@eombor.uz",
                "password": "Account123!",
                "first_name": "Jasur",
                "last_name": "Nurmuhamedov",
                "phone": "+998901111114",
                "stir_inn": "123456789015",
                "roles": ["accountant"],
                "branch": branch_main,
            },
            {
                "email": "warehouse@eombor.uz",
                "password": "Warehouse123!",
                "first_name": "Kamola",
                "last_name": "Saidova",
                "phone": "+998901111115",
                "stir_inn": "123456789016",
                "roles": ["warehouse"],
                "branch": branch_main,
            },
            {
                "email": "prorab@eombor.uz",
                "password": "Prorab123!",
                "first_name": "Bekzod",
                "last_name": "Tursunov",
                "phone": "+998901111116",
                "stir_inn": "123456789017",
                "roles": ["prorab"],
                "branch": branch_secondary,
            },
            {
                "email": "branch@eombor.uz",
                "password": "Branch123!",
                "first_name": "Gulnora",
                "last_name": "Raximova",
                "phone": "+998901111117",
                "stir_inn": "123456789018",
                "roles": ["branch_manager"],
                "branch": branch_secondary,
            },
            {
                "email": "architecture@eombor.uz",
                "password": "Arch12345!",
                "first_name": "Sherzod",
                "last_name": "Abdullaev",
                "phone": "+998901111118",
                "stir_inn": "123456789019",
                "roles": ["architecture"],
                "branch": branch_main,
            },
            {
                "email": "site.engineer@eombor.uz",
                "password": "Engineer123!",
                "first_name": "Aziza",
                "last_name": "Qodirova",
                "phone": "+998901111119",
                "stir_inn": "123456789020",
                "roles": ["architecture", "procurement"],
                "branch": branch_third,
            },
        ]
        self.demo_passwords = {}
        users = []
        for spec in user_specs:
            defaults = {k: v for k, v in spec.items() if k not in {"email", "password"}}
            user, created = User.objects.get_or_create(email=spec["email"], defaults=defaults)
            if created or not user.check_password(spec["password"]):
                user.first_name = spec["first_name"]
                user.last_name = spec["last_name"]
                user.phone = spec["phone"]
                user.stir_inn = spec["stir_inn"]
                user.roles = spec["roles"]
                user.branch = spec["branch"]
                user.is_active = True
                user.is_staff = spec.get("is_staff", False)
                user.is_superuser = spec.get("is_superuser", False)
                user.set_password(spec["password"])
                user.save()
            self.demo_passwords[user.email] = spec["password"]
            users.append(user)
        return users

    def _seed_sites(self, branches, users):
        branch_main, branch_secondary, branch_third = branches
        prorab = self._user_by_email(users, "prorab@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")
        site_specs = [
            {
                "code": "SITE-001",
                "name": "Toshkent City Mall",
                "branch": branch_main,
                "address": "Toshkent sh., Chilonzor tumani, Qatortol ko'chasi 7",
                "status": "active",
                "budget": Decimal("12500000.00"),
                "prorab": prorab,
            },
            {
                "code": "SITE-002",
                "name": "Samarqand Business Center",
                "branch": branch_secondary,
                "address": "Samarqand sh., Registon ko'chasi 44",
                "status": "paused",
                "budget": Decimal("8400000.00"),
                "prorab": prorab,
            },
            {
                "code": "SITE-003",
                "name": "Yangi Uy-2 Turar Joy",
                "branch": branch_main,
                "address": "Toshkent vil., Bekobod tumani, Navro'z massivi",
                "status": "completed",
                "budget": Decimal("6400000.00"),
                "prorab": prorab,
            },
            {
                "code": "SITE-004",
                "name": "Farg'ona Logistics Hub",
                "branch": branch_third,
                "address": "Farg'ona sh., Alisher Navoiy ko'chasi 9",
                "status": "active",
                "budget": Decimal("11800000.00"),
                "prorab": site_engineer,
            },
            {
                "code": "SITE-005",
                "name": "Qo'qon Residential Block",
                "branch": branch_third,
                "address": "Qo'qon sh., Marg'ilon yo'li 14",
                "status": "paused",
                "budget": Decimal("7200000.00"),
                "prorab": site_engineer,
            },
        ]
        sites = []
        for spec in site_specs:
            site, _ = ConstructionSite.objects.get_or_create(code=spec["code"], defaults=spec)
            sites.append(site)
        return sites

    def _seed_warehouses(self, branches):
        branch_main, branch_secondary, branch_third = branches
        warehouse_specs = [
            {
                "code": "WH-TSH-01",
                "name": "Toshkent Markaziy Ombori",
                "branch": branch_main,
                "address": "Toshkent sh., Sergeli tumani, Industrial zonasi 3",
            },
            {
                "code": "WH-SAM-01",
                "name": "Samarqand Ombori",
                "branch": branch_secondary,
                "address": "Samarqand sh., Farhod ko'chasi 18",
            },
            {
                "code": "WH-FRG-01",
                "name": "Farg'ona Ta'minot Ombori",
                "branch": branch_third,
                "address": "Farg'ona sh., Qurilishchilar ko'chasi 6",
            },
        ]
        warehouses = []
        for spec in warehouse_specs:
            warehouse, _ = Warehouse.objects.get_or_create(code=spec["code"], defaults=spec)
            warehouses.append(warehouse)
        return warehouses

    def _seed_materials(self):
        material_specs = [
            {
                "code": "MAT-CEM-01",
                "name": "Portland sement",
                "unit": "qop",
                "category": "Qurilish materiallari",
                "description": "50 kg li qoplarda sement",
            },
            {
                "code": "MAT-ARM-01",
                "name": "Armatura 12 mm",
                "unit": "tonna",
                "category": "Metall",
                "description": "12 mm diametrli armatura",
            },
            {
                "code": "MAT-QUM-01",
                "name": "Qum",
                "unit": "m3",
                "category": "Inert materiallar",
                "description": "Tozalangan qurilish qumi",
            },
            {
                "code": "MAT-G'IS-01",
                "name": "G'isht",
                "unit": "dona",
                "category": "Devor materiallari",
                "description": "Qizil pishiq g'isht",
            },
            {
                "code": "MAT-MET-01",
                "name": "Metall profil",
                "unit": "dona",
                "category": "Metall",
                "description": "60x60 metall profil",
            },
            {
                "code": "MAT-KAB-01",
                "name": "Elektr kabel",
                "unit": "metr",
                "category": "Elektrika",
                "description": "NYM 3x2.5 kabel",
            },
            {
                "code": "MAT-SHF-01",
                "name": "Shifer",
                "unit": "varaq",
                "category": "Tom yopish",
                "description": "Sanoat tomi uchun shifer",
            },
            {
                "code": "MAT-PLS-01",
                "name": "Plitka",
                "unit": "m2",
                "category": "Ichki pardoz",
                "description": "Pol va devor plitkasi",
            },
            {
                "code": "MAT-BOY-01",
                "name": "Bo'yoq",
                "unit": "litr",
                "category": "Pardoz",
                "description": "Ichki va tashqi bo'yoq",
            },
            {
                "code": "MAT-QOL-01",
                "name": "Qolip taxtasi",
                "unit": "dona",
                "category": "Yordamchi materiallar",
                "description": "Beton quyish uchun qolip taxtasi",
            },
        ]
        materials = []
        for spec in material_specs:
            material, _ = Material.objects.get_or_create(code=spec["code"], defaults=spec)
            materials.append(material)
        return materials

    def _seed_suppliers(self):
        supplier_specs = [
            {
                "code": "SUP-001",
                "name": "UzBuild Trade",
                "contact_person": "Azizbek Xudoyberdiyev",
                "phone": "+998711110001",
                "email": "sales@uzbuild.uz",
                "address": "Toshkent sh., Yakkasaroy tumani, Bobur ko'chasi 24",
            },
            {
                "code": "SUP-002",
                "name": "Samarqand Metal Supply",
                "contact_person": "Shahnoza Ismatova",
                "phone": "+998661110002",
                "email": "info@sammet.uz",
                "address": "Samarqand sh., Ibn Sino ko'chasi 15",
            },
            {
                "code": "SUP-003",
                "name": "Concrete Line",
                "contact_person": "Rustam Toirov",
                "phone": "+998781110003",
                "email": "order@concreteline.uz",
                "address": "Toshkent sh., Yangihayot tumani, Beton massiv 1",
            },
            {
                "code": "SUP-004",
                "name": "Farg'ona Build Market",
                "contact_person": "Muzaffar Jalilov",
                "phone": "+998733110004",
                "email": "sales@fbm.uz",
                "address": "Farg'ona sh., Sayilgoh ko'chasi 11",
            },
            {
                "code": "SUP-005",
                "name": "Universal Finish",
                "contact_person": "Dilnoza Karimova",
                "phone": "+998712220005",
                "email": "info@unifinish.uz",
                "address": "Toshkent sh., Chilonzor tumani, Zargarlik ko'chasi 3",
            },
        ]
        suppliers = []
        for spec in supplier_specs:
            supplier, _ = Supplier.objects.get_or_create(code=spec["code"], defaults=spec)
            suppliers.append(supplier)
        return suppliers

    def _seed_addresses(self):
        address_specs = [
            {"city": "Toshkent", "district": "Yunusobod", "street": "Amir Temur", "building": "108"},
            {"city": "Samarqand", "district": "Siyob", "street": "Registon", "building": "44"},
            {"city": "Toshkent", "district": "Chilonzor", "street": "Qatortol", "building": "7"},
            {"city": "Bekobod", "district": "Navro'z", "street": "Massiv", "building": "2"},
            {"city": "Farg'ona", "district": "Qirguli", "street": "Mustaqillik", "building": "25"},
            {"city": "Qo'qon", "district": "Markaz", "street": "Marg'ilon yo'li", "building": "14"},
        ]
        addresses = []
        for spec in address_specs:
            address, _ = Address.objects.get_or_create(**spec)
            addresses.append(address)
        return addresses

    def _seed_documents(self, branches, sites, users):
        branch_main, branch_secondary, branch_third = branches
        architecture = self._user_by_email(users, "architecture@eombor.uz")
        ceo = self._user_by_email(users, "ceo@eombor.uz")
        procurement = self._user_by_email(users, "procurement@eombor.uz")
        accountant = self._user_by_email(users, "accountant@eombor.uz")
        warehouse_user = self._user_by_email(users, "warehouse@eombor.uz")
        prorab = self._user_by_email(users, "prorab@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")

        doc_specs = [
            {
                "doc_number": "PR-20260709-0001",
                "doc_type": "purchase_request",
                "status": "created",
                "title": "Sement va armatura xaridi",
                "description": "Toshkent obyekti uchun sement, armatura va qum kerak.",
                "created_by": prorab,
                "site": sites[0],
                "branch": branch_main,
                "total_amount": Decimal("145000000.00"),
                "notes": "Shoshilinch zaxira to'ldirish.",
            },
            {
                "doc_number": "PR-20260709-0002",
                "doc_type": "purchase_request",
                "status": "architecture",
                "title": "Elektr kabel va profil",
                "description": "Loyiha bo'yicha kabel va metall profil xaridi.",
                "created_by": procurement,
                "site": sites[1],
                "branch": branch_secondary,
                "total_amount": Decimal("86000000.00"),
                "notes": "Arxitektura tasdig'ini kutmoqda.",
            },
            {
                "doc_number": "PR-20260709-0003",
                "doc_type": "purchase_request",
                "status": "ceo",
                "title": "G'isht va sement zaxirasi",
                "description": "2-obyekt uchun g'isht va sement so'rovi.",
                "created_by": prorab,
                "site": sites[2],
                "branch": branch_main,
                "total_amount": Decimal("93000000.00"),
                "notes": "Rais tasdig'ida.",
            },
            {
                "doc_number": "CT-20260709-0001",
                "doc_type": "contract",
                "status": "contract",
                "title": "UzBuild Trade shartnomasi",
                "description": "Sement yetkazib berish bo'yicha shartnoma.",
                "created_by": procurement,
                "site": sites[0],
                "branch": branch_main,
                "total_amount": Decimal("145000000.00"),
                "notes": "Shartnoma tayyor.",
            },
            {
                "doc_number": "IV-20260709-0001",
                "doc_type": "invoice",
                "status": "payment",
                "title": "1-oy hisob-faktura",
                "description": "Sement va armatura uchun invoice.",
                "created_by": accountant,
                "site": sites[0],
                "branch": branch_main,
                "total_amount": Decimal("87000000.00"),
                "notes": "To'lov kutilmoqda.",
            },
            {
                "doc_number": "IV-20260709-0002",
                "doc_type": "invoice",
                "status": "delivering",
                "title": "Yetkazib berish invoice",
                "description": "Kabel va profil uchun invoice.",
                "created_by": accountant,
                "site": sites[1],
                "branch": branch_secondary,
                "total_amount": Decimal("46000000.00"),
                "notes": "Yo'lda.",
            },
            {
                "doc_number": "PR-20260709-0004",
                "doc_type": "purchase_request",
                "status": "approved",
                "title": "Ombor to'ldirish so'rovi",
                "description": "Markaziy ombor uchun qo'shimcha materiallar.",
                "created_by": warehouse_user,
                "site": sites[0],
                "branch": branch_main,
                "total_amount": Decimal("52000000.00"),
                "notes": "Xaridga ruxsat berildi.",
            },
            {
                "doc_number": "CT-20260709-0002",
                "doc_type": "contract",
                "status": "received",
                "title": "Concrete Line shartnomasi",
                "description": "Beton aralashma yetkazib berish bo'yicha.",
                "created_by": procurement,
                "site": sites[2],
                "branch": branch_main,
                "total_amount": Decimal("310000000.00"),
                "notes": "Qabul qilindi.",
            },
            {
                "doc_number": "IV-20260709-0003",
                "doc_type": "invoice",
                "status": "closed",
                "title": "Yopilgan invoice",
                "description": "To'liq yopilgan hisob-faktura.",
                "created_by": accountant,
                "site": sites[2],
                "branch": branch_main,
                "total_amount": Decimal("125000000.00"),
                "notes": "Hisob yopildi.",
            },
            {
                "doc_number": "PR-20260709-0005",
                "doc_type": "purchase_request",
                "status": "rejected",
                "title": "Bekor qilingan so'rov",
                "description": "Takroriy buyurtma rad etildi.",
                "created_by": prorab,
                "site": sites[1],
                "branch": branch_secondary,
                "total_amount": Decimal("26000000.00"),
                "notes": "Rad etildi.",
            },
            {
                "doc_number": "PR-20260709-0006",
                "doc_type": "purchase_request",
                "status": "architecture",
                "title": "Farg'ona loyiha inventari",
                "description": "Farg'ona obyektlari uchun qo'shimcha inventar va asboblar.",
                "created_by": site_engineer,
                "site": sites[3],
                "branch": branch_third,
                "total_amount": Decimal("78000000.00"),
                "notes": "Arxitektura ko'rigida.",
            },
            {
                "doc_number": "CT-20260709-0003",
                "doc_type": "contract",
                "status": "contract",
                "title": "Farg'ona Build Market shartnomasi",
                "description": "Ichki pardoz materiallari bo'yicha shartnoma.",
                "created_by": procurement,
                "site": sites[3],
                "branch": branch_third,
                "total_amount": Decimal("78000000.00"),
                "notes": "Yangi filial uchun.",
            },
            {
                "doc_number": "IV-20260709-0004",
                "doc_type": "invoice",
                "status": "payment",
                "title": "Qo'shimcha to'lov invoice",
                "description": "Plitka va bo'yoq uchun invoice.",
                "created_by": accountant,
                "site": sites[4],
                "branch": branch_third,
                "total_amount": Decimal("62000000.00"),
                "notes": "To'lov jarayonida.",
            },
        ]

        documents = []
        for spec in doc_specs:
            document, _ = Document.objects.get_or_create(
                doc_number=spec["doc_number"],
                defaults=spec,
            )
            documents.append(document)
        return documents

    def _seed_document_approvals(self, documents, users):
        architecture = self._user_by_email(users, "architecture@eombor.uz")
        ceo = self._user_by_email(users, "ceo@eombor.uz")
        procurement = self._user_by_email(users, "procurement@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")
        approvals = [
            (documents[1], architecture, "approved", "Loyiha talablariga mos."),
            (documents[2], ceo, "approved", "Budjet bo'yicha ma'qullandi."),
            (documents[3], procurement, "approved", "Shartnoma tuzishga ruxsat."),
            (documents[4], procurement, "approved", "To'lov bosqichiga o'tkazildi."),
            (documents[7], procurement, "approved", "Qabul qilish dalolatnomasi tayyor."),
            (documents[10], site_engineer, "approved", "Farg'ona filialiga mos."),
            (documents[11], procurement, "approved", "Yangi filial shartnomasi ma'qullandi."),
        ]
        for document, approver, action, comment in approvals:
            DocumentApproval.objects.get_or_create(
                document=document,
                approver=approver,
                action=action,
                defaults={"comment": comment},
            )

    def _seed_purchase_orders(self, documents, suppliers, materials):
        po_specs = [
            {
                "document": documents[0],
                "supplier": suppliers[0],
                "items": [
                    (materials[0], Decimal("1000"), Decimal("54000.00")),
                    (materials[1], Decimal("15"), Decimal("4800000.00")),
                ],
            },
            {
                "document": documents[3],
                "supplier": suppliers[2],
                "items": [
                    (materials[2], Decimal("450"), Decimal("180000.00")),
                    (materials[3], Decimal("35000"), Decimal("1800.00")),
                ],
            },
            {
                "document": documents[10],
                "supplier": suppliers[3],
                "items": [
                    (materials[6], Decimal("1200"), Decimal("35000.00")),
                    (materials[7], Decimal("1800"), Decimal("95000.00")),
                ],
            },
        ]
        for spec in po_specs:
            purchase_order, _ = PurchaseOrder.objects.get_or_create(
                document=spec["document"],
                defaults={"supplier": spec["supplier"]},
            )
            if purchase_order.supplier_id != spec["supplier"].id:
                purchase_order.supplier = spec["supplier"]
                purchase_order.save(update_fields=["supplier"])

            for material, quantity, unit_price in spec["items"]:
                PurchaseOrderItem.objects.get_or_create(
                    purchase_order=purchase_order,
                    material=material,
                    defaults={
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": quantity * unit_price,
                    },
                )

    def _seed_contracts(self, documents, suppliers):
        contract_specs = [
            {
                "document": documents[3],
                "supplier": suppliers[0],
                "contract_number": "CTR-20260709-001",
                "signed_date": timezone.localdate(),
                "start_date": timezone.localdate(),
                "end_date": timezone.localdate().replace(year=timezone.localdate().year + 1),
                "total_amount": Decimal("145000000.00"),
                "description": "Sement yetkazib berish bo'yicha yillik shartnoma.",
            },
            {
                "document": documents[7],
                "supplier": suppliers[2],
                "contract_number": "CTR-20260709-002",
                "signed_date": timezone.localdate(),
                "start_date": timezone.localdate(),
                "end_date": timezone.localdate().replace(year=timezone.localdate().year + 1),
                "total_amount": Decimal("310000000.00"),
                "description": "Beton aralashma yetkazib berish bo'yicha shartnoma.",
            },
            {
                "document": documents[11],
                "supplier": suppliers[3],
                "contract_number": "CTR-20260709-003",
                "signed_date": timezone.localdate(),
                "start_date": timezone.localdate(),
                "end_date": timezone.localdate().replace(year=timezone.localdate().year + 1),
                "total_amount": Decimal("78000000.00"),
                "description": "Farg'ona filialiga ta'minot shartnomasi.",
            },
        ]
        contracts = []
        for spec in contract_specs:
            contract, _ = Contract.objects.get_or_create(
                document=spec["document"],
                defaults=spec,
            )
            contracts.append(contract)
        return contracts

    def _seed_invoices(self, documents, contracts):
        invoice_specs = [
            {
                "document": documents[4],
                "contract": contracts[0],
                "invoice_number": "INV-20260709-001",
                "invoice_date": timezone.localdate(),
                "due_date": timezone.localdate(),
                "total_amount": Decimal("87000000.00"),
                "paid_amount": Decimal("25000000.00"),
                "payment_status": "partial",
            },
            {
                "document": documents[5],
                "contract": contracts[1],
                "invoice_number": "INV-20260709-002",
                "invoice_date": timezone.localdate(),
                "due_date": timezone.localdate(),
                "total_amount": Decimal("46000000.00"),
                "paid_amount": Decimal("0.00"),
                "payment_status": "unpaid",
            },
            {
                "document": documents[8],
                "contract": contracts[1],
                "invoice_number": "INV-20260709-003",
                "invoice_date": timezone.localdate(),
                "due_date": timezone.localdate(),
                "total_amount": Decimal("125000000.00"),
                "paid_amount": Decimal("125000000.00"),
                "payment_status": "paid",
            },
            {
                "document": documents[12],
                "contract": contracts[2],
                "invoice_number": "INV-20260709-004",
                "invoice_date": timezone.localdate(),
                "due_date": timezone.localdate(),
                "total_amount": Decimal("62000000.00"),
                "paid_amount": Decimal("12000000.00"),
                "payment_status": "partial",
            },
        ]
        invoices = []
        for spec in invoice_specs:
            invoice, _ = Invoice.objects.get_or_create(
                document=spec["document"],
                defaults=spec,
            )
            invoices.append(invoice)
        return invoices

    def _seed_payments(self, invoices, users):
        accountant = self._user_by_email(users, "accountant@eombor.uz")
        payment_specs = [
            {
                "invoice": invoices[0],
                "amount": Decimal("25000000.00"),
                "payment_method": "bank transfer",
                "reference_number": "PAY-20260709-001",
                "performed_by": accountant,
                "notes": "Qisman to'lov amalga oshirildi.",
            },
            {
                "invoice": invoices[2],
                "amount": Decimal("125000000.00"),
                "payment_method": "bank transfer",
                "reference_number": "PAY-20260709-002",
                "performed_by": accountant,
                "notes": "To'liq yopildi.",
            },
            {
                "invoice": invoices[3],
                "amount": Decimal("12000000.00"),
                "payment_method": "bank transfer",
                "reference_number": "PAY-20260709-003",
                "performed_by": accountant,
                "notes": "Farg'ona filialiga dastlabki to'lov.",
            },
        ]
        for spec in payment_specs:
            Payment.objects.get_or_create(
                reference_number=spec["reference_number"],
                defaults=spec,
            )

    def _seed_inventory(self, warehouses, materials):
        inventory_specs = [
            (warehouses[0], materials[0], Decimal("1200.000"), Decimal("300.000")),
            (warehouses[0], materials[1], Decimal("22.500"), Decimal("5.000")),
            (warehouses[0], materials[2], Decimal("180.000"), Decimal("60.000")),
            (warehouses[1], materials[3], Decimal("54000.000"), Decimal("12000.000")),
            (warehouses[1], materials[4], Decimal("180.000"), Decimal("40.000")),
            (warehouses[1], materials[5], Decimal("7500.000"), Decimal("1200.000")),
            (warehouses[2], materials[6], Decimal("900.000"), Decimal("250.000")),
            (warehouses[2], materials[7], Decimal("1400.000"), Decimal("300.000")),
            (warehouses[2], materials[8], Decimal("800.000"), Decimal("200.000")),
            (warehouses[2], materials[9], Decimal("160.000"), Decimal("50.000")),
        ]
        for warehouse, material, quantity, min_quantity in inventory_specs:
            InventoryItem.objects.get_or_create(
                warehouse=warehouse,
                material=material,
                defaults={"quantity": quantity, "min_quantity": min_quantity},
            )

    def _seed_stock_movements(self, warehouses, materials, users):
        warehouse_user = self._user_by_email(users, "warehouse@eombor.uz")
        movement_specs = [
            {
                "warehouse": warehouses[0],
                "material": materials[0],
                "movement_type": "IN",
                "quantity": Decimal("500.000"),
                "performed_by": warehouse_user,
                "notes": "Yangi sement partiyasi qabul qilindi.",
            },
            {
                "warehouse": warehouses[0],
                "material": materials[1],
                "movement_type": "OUT",
                "quantity": Decimal("2.500"),
                "performed_by": warehouse_user,
                "notes": "Obyektga armatura chiqarildi.",
            },
            {
                "warehouse": warehouses[1],
                "material": materials[3],
                "movement_type": "IN",
                "quantity": Decimal("15000.000"),
                "performed_by": warehouse_user,
                "notes": "G'isht qabul qilindi.",
            },
            {
                "warehouse": warehouses[1],
                "material": materials[5],
                "movement_type": "TRANSFER",
                "quantity": Decimal("1000.000"),
                "performed_by": warehouse_user,
                "notes": "Kabel boshqa omborga ko'chirildi.",
            },
            {
                "warehouse": warehouses[2],
                "material": materials[6],
                "movement_type": "IN",
                "quantity": Decimal("300.000"),
                "performed_by": warehouse_user,
                "notes": "Shifer qabul qilindi.",
            },
            {
                "warehouse": warehouses[2],
                "material": materials[8],
                "movement_type": "OUT",
                "quantity": Decimal("90.000"),
                "performed_by": warehouse_user,
                "notes": "Bo'yoq ichki pardozga chiqarildi.",
            },
        ]
        for spec in movement_specs:
            unique_note = spec["notes"]
            StockMovement.objects.get_or_create(
                warehouse=spec["warehouse"],
                material=spec["material"],
                movement_type=spec["movement_type"],
                quantity=spec["quantity"],
                performed_by=spec["performed_by"],
                notes=unique_note,
            )

    def _seed_document_files(self, documents, users):
        uploader = self._user_by_email(users, "procurement@eombor.uz")
        file_specs = [
            (documents[3], "contract_summary.pdf", "Shartnoma bo'yicha demo fayl."),
            (documents[4], "invoice_scan.pdf", "Invoice skan nusxasi."),
            (documents[0], "purchase_request.xlsx", "Xarid so'rovi demo jadvali."),
            (documents[10], "fargona_purchase_request.pdf", "Farg'ona filialining demo hujjati."),
            (documents[11], "fargona_contract.pdf", "Farg'ona filialiga tegishli demo kontrakt."),
        ]
        for document, filename, text in file_specs:
            content = ContentFile(text.encode("utf-8"))
            content.name = filename
            DocumentFile.objects.get_or_create(
                document=document,
                original_filename=filename,
                defaults={
                    "file": content,
                    "file_size": len(text.encode("utf-8")),
                    "uploaded_by": uploader,
                },
            )

    def _seed_production_requests(self, sites, users):
        prorab = self._user_by_email(users, "prorab@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")
        request_specs = [
            {
                "site": sites[0],
                "request_number": "PRD-20260709-001",
                "title": "Beton quyish uchun qo'shimcha armatura",
                "description": "1-obyekt uchun qo'shimcha armatura kerak.",
                "status": "pending",
                "created_by": prorab,
            },
            {
                "site": sites[1],
                "request_number": "PRD-20260709-002",
                "title": "Oynalar uchun profil",
                "description": "Fasad ishlari uchun profil va kabel kerak.",
                "status": "approved",
                "created_by": prorab,
            },
            {
                "site": sites[2],
                "request_number": "PRD-20260709-003",
                "title": "Yakuniy tozalash anjomlari",
                "description": "Topshirishdan oldin tozalash materiallari so'raladi.",
                "status": "delivered",
                "created_by": prorab,
            },
            {
                "site": sites[3],
                "request_number": "PRD-20260709-004",
                "title": "Farg'ona ombori uchun qoplama",
                "description": "Yangi ombor qoplama materiallari kerak.",
                "status": "approved",
                "created_by": site_engineer,
            },
            {
                "site": sites[4],
                "request_number": "PRD-20260709-005",
                "title": "Qo'qon blokiga bo'yoq",
                "description": "Ichki pardoz uchun bo'yoq so'raladi.",
                "status": "pending",
                "created_by": site_engineer,
            },
        ]
        for spec in request_specs:
            ProductionRequest.objects.get_or_create(
                request_number=spec["request_number"],
                defaults=spec,
            )

    def _seed_tickets(self, branches, sites, users):
        branch_main, branch_secondary, branch_third = branches
        prorab = self._user_by_email(users, "prorab@eombor.uz")
        warehouse_user = self._user_by_email(users, "warehouse@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")
        ticket_specs = [
            {
                "title": "Sement zaxirasi kamayib ketdi",
                "description": "Markaziy omborda sement 10 qopdan kam qoldi.",
                "category": "material_shortage",
                "priority": "high",
                "status": "open",
                "created_by": prorab,
                "assigned_to": warehouse_user,
                "branch": branch_main,
                "site": sites[0],
                "response": "",
            },
            {
                "title": "Generator kerak",
                "description": "Tungi ishlar uchun generator ijarasi kerak.",
                "category": "equipment",
                "priority": "medium",
                "status": "in_progress",
                "created_by": prorab,
                "assigned_to": warehouse_user,
                "branch": branch_secondary,
                "site": sites[1],
                "response": "Texnika bo'limiga yuborildi.",
            },
            {
                "title": "Qo'shimcha ishchilar talab etiladi",
                "description": "Fasad montaji uchun qo'shimcha brigada kerak.",
                "category": "labor",
                "priority": "urgent",
                "status": "resolved",
                "created_by": prorab,
                "assigned_to": warehouse_user,
                "branch": branch_main,
                "site": sites[2],
                "response": "Brigada biriktirildi.",
            },
            {
                "title": "Hisobotdagi raqamlar tekshirilsin",
                "description": "Ichki audit bo'yicha hujjatlar qayta ko'rib chiqilsin.",
                "category": "other",
                "priority": "low",
                "status": "closed",
                "created_by": prorab,
                "assigned_to": warehouse_user,
                "branch": branch_secondary,
                "site": None,
                "response": "Masala yopildi.",
            },
            {
                "title": "Farg'ona omborida shifer yetishmayapti",
                "description": "Yangi obyekt uchun shifer zaxirasi nolga tushdi.",
                "category": "material_shortage",
                "priority": "high",
                "status": "open",
                "created_by": site_engineer,
                "assigned_to": warehouse_user,
                "branch": branch_third,
                "site": sites[3],
                "response": "",
            },
            {
                "title": "Qo'qon blokiga elektrchilar kerak",
                "description": "Ichki ishlarda elektr montaj brigadasi kerak.",
                "category": "labor",
                "priority": "medium",
                "status": "in_progress",
                "created_by": site_engineer,
                "assigned_to": warehouse_user,
                "branch": branch_third,
                "site": sites[4],
                "response": "Brigada navbatga qo'yildi.",
            },
        ]
        for spec in ticket_specs:
            Ticket.objects.get_or_create(
                title=spec["title"],
                created_by=spec["created_by"],
                defaults=spec,
            )

    def _seed_notifications(self, users):
        admin = self._user_by_email(users, "admin@eombor.uz")
        ceo = self._user_by_email(users, "ceo@eombor.uz")
        procurement = self._user_by_email(users, "procurement@eombor.uz")
        accountant = self._user_by_email(users, "accountant@eombor.uz")
        warehouse_user = self._user_by_email(users, "warehouse@eombor.uz")
        prorab = self._user_by_email(users, "prorab@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")

        notification_specs = [
            (admin, "Tizim tayyor", "Demo ma'lumotlar muvaffaqiyatli qo'shildi.", "info"),
            (ceo, "Yangi tasdiqlash", "20260709-0003 hujjati tasdiqlashda.", "warning"),
            (procurement, "Shartnoma tayyor", "Yangi kontrakt imzolashga tayyor.", "success"),
            (accountant, "To'lov kutilmoqda", "INV-20260709-001 bo'yicha qisman to'lov bor.", "warning"),
            (warehouse_user, "Ombor zaxirasi", "Sement zaxirasi minimal darajaga yaqin.", "info"),
            (prorab, "Zayavka qabul qilindi", "PRD-20260709-001 ishlab chiqishga qabul qilindi.", "success"),
            (site_engineer, "Farg'ona bo'limi", "Farg'ona filialida yangi topshiriqlar bor.", "info"),
            (warehouse_user, "Yangi yetkazib berish", "Shifer va bo'yoq partiyasi kutilmoqda.", "warning"),
        ]
        for user, title, message, notification_type in notification_specs:
            Notification.objects.get_or_create(
                user=user,
                title=title,
                defaults={"message": message, "notification_type": notification_type},
            )

    def _seed_audit_logs(self, users, documents, suppliers, sites, warehouses):
        admin = self._user_by_email(users, "admin@eombor.uz")
        procurement = self._user_by_email(users, "procurement@eombor.uz")
        warehouse_user = self._user_by_email(users, "warehouse@eombor.uz")
        site_engineer = self._user_by_email(users, "site.engineer@eombor.uz")
        audit_specs = [
            (admin, "seed_demo_data", "System", None, {"status": "completed"}, "127.0.0.1"),
            (procurement, "document_created", "Document", documents[0].id, {"doc_number": documents[0].doc_number}, "127.0.0.1"),
            (procurement, "supplier_added", "Supplier", suppliers[0].id, {"code": suppliers[0].code}, "127.0.0.1"),
            (warehouse_user, "inventory_updated", "InventoryItem", None, {"warehouse": warehouses[0].code if warehouses else None}, "127.0.0.1"),
            (admin, "site_created", "ConstructionSite", sites[0].id, {"code": sites[0].code}, "127.0.0.1"),
            (site_engineer, "request_created", "ProductionRequest", None, {"site": sites[3].code}, "127.0.0.1"),
            (procurement, "contract_signed", "Contract", documents[11].id if len(documents) > 11 else None, {"doc_number": documents[11].doc_number if len(documents) > 11 else None}, "127.0.0.1"),
        ]
        for user, action, model_name, object_id, details, ip_address in audit_specs:
            AuditLog.objects.get_or_create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=object_id,
                defaults={"details": details, "ip_address": ip_address},
            )

    def _user_by_email(self, users, email: str):
        for user in users:
            if user.email == email:
                return user
        raise KeyError(f"User not found: {email}")
