# E-Ombor Platform

O'zbekiston davlat xizmatlari va tashkilotlar uchun mo'ljallangan birlashtirilgan boshqaruv platformasi.

## 📋 Mazmuni

- [🏗 Arxitektura](#-arxitektura)
- [✨ Xususiyatlar](#-xususiyarlar)
- [🚀 Tezkor boshlash](#-tezkor-boshlash)
- [📡 API Hujjatlari](#-api-hujjatlari)
- [🗄 Ma'lumotlar modeli](#-ma'lumotlar-modeli)
- [🔐 Xavfsizlik](#-xavfsizlik)
- [📦 Loyiha tuzilishi](#-loyiha-tuzilishi)
- [🔮 Keyingi bosqichlar](#-keyingi-bosqichlar)

---

## 🏗 Arxitektura

```
┌─────────────────────────────────────────────────────────────┐
│                      Foydalanuvchi (Browser)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────▼──────────────────────────────────┐
│                    React + Vite (Frontend)                   │
│  - SPA ilova (react-router-dom)                              │
│  - Axios orqali API bilan muloqot                            │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│              Django REST Framework (Backend)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │   Auth       │  │  Views       │  │  Serializers      │   │
│  │  JWT Token   │  │  APIViews    │  │  DRF              │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Models (Django ORM)                        │ │
│  │  User │ Document │ PurchaseOrder │ Invoice │ Ticket     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    SQLite / PostgreSQL                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Xususiyatlar

### 🔐 Autentifikatsiya va Avtorizatsiya
- Ro'yxatdan o'tish va kirish (JWT token)
- Foydalanuvchi rollari (admin, foydalanuvchi)
- Profilni ko'rish va tahrirlash
- Parolni o'zgartirish

### 📄 Hujjat boshqaruvi
- Hujjatlarni yaratish, ko'rish, tahrirlash va o'chirish
- Hujjat turlari (buyurtma, akt, hisobot va b.)
- Hujjat fayllarini yuklash (PDF, rasm, hujjat — max 10MB)
- Har bir hujjatga biriktirilgan fayllar ro'yxati

### 🏭 Ishlab chiqarish ob'ektlari
- Tashkilot sho'ba bo'limlari (Branch)
- Qurilish maydonchalari (ConstructionSite)
- Omborxonalar (Warehouse)
- Materiallar va inventarizatsiya (Material, InventoryItem)
- Ombor harakatlari (kirish/chiqish)

### 🛒 Xarid va Yetkazib beruvchilar
- Yetkazib beruvchilar bazasi (Supplier)
- Xarid buyurtmalari (PurchaseOrder)
- Buyurtma bandlari (PurchaseOrderItem)

### 💰 Moliya bo'limi
- **Shartnomalar** (Contract) — raqam, sana, summa
- **Hisob-fakturalar** (Invoice) — to'lov holati: to'lanmagan / qisman / to'liq
- **To'lovlar** (Payment) — avtomatik hisob-faktura yangilanishi

### 📋 Ishlab chiqarish zayavkalari
- Qurilish maydonchasidan zayavka yaratish
- Avtomatik raqam generatsiya (PR-YYYYMMDD-XXXX)
- Holat kuzatish: kutilmoqda → tasdiqlandi → yetkazildi → bekor qilindi

### 🎫 Murojaat tizimi (Ticketing)
- Kategoriya: material yetishmasligi, texnika, ishchi kuchi, boshqa
- Ustuvorlik: past, o'rta, yuqori, shoshilinch
- Holat: ochiq → jarayonda → yechildi → yopildi
- Foydalanuvchiga faqat o'z murojaatlari ko'rinadi (staff — barchasi)

### 📍 Manzillar
- Shahar, tuman, ko'cha, bino bo'yicha tizimlashtirish
- Noyob kombinatsiya tekshiruvi

### 📊 Dashboard
- Umumiy statistika: foydalanuvchilar, hujjatlar, ombor, buyurtmalar
- Kam qolgan materiallar
- So'nggi hujjatlar
- O'qilmagan bildirishnomalar

### 🔔 Bildirishnomalar
- Yaratilgan va tahrirlangan hujjatlar haqida
- O'qilgan deb belgilash va hammasini o'qish

---

## 🚀 Tezkor boshlash

### Talablar
- Python 3.9+
- Node.js 16+
- (ixtiyoriy) PostgreSQL 14+

### Backend o'rnatish

```bash
cd backend

# Virtual muhit yaratish
python3 -m venv venv
source venv/bin/activate

# Bog'liqliklarni o'rnatish
pip install -r requirements.txt

# Ma'lumotlar bazasini migratsiya qilish
python manage.py migrate

# Superuser yaratish (boshqaruv paneli uchun)
python manage.py createsuperuser

# Dev serverni ishga tushirish
python manage.py runserver
```

Backend `http://localhost:3000` da ishga tushadi.
DRF Swagger hujjatlari: `http://localhost:3000/api/schema/swagger-ui/`

### Frontend o'rnatish

```bash
cd frontend

# Bog'liqliklarni o'rnatish
npm install

# Dev serverni ishga tushirish
npm run dev
```

Frontend `http://localhost:5173` da ishga tushadi.

### Backend .env sozlamalari

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DB_NAME=eombor
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### Demo ma'lumotlar

Backend tayyor bo'lgach:

```bash
cd backend
python3 manage.py seed_demo_data
```

Demo loginlar:

- `admin@eombor.uz` / `Admin123!`
- `ceo@eombor.uz` / `Ceo12345!`
- `procurement@eombor.uz` / `Procure123!`
- `accountant@eombor.uz` / `Account123!`
- `warehouse@eombor.uz` / `Warehouse123!`
- `prorab@eombor.uz` / `Prorab123!`
- `branch@eombor.uz` / `Branch123!`
- `architecture@eombor.uz` / `Arch12345!`
- `site.engineer@eombor.uz` / `Engineer123!`

---

## 📡 API Hujjatlari

### Autentifikatsiya

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| POST | `/api/auth/register/` | Yangi foydalanuvchi ro'yxatdan o'tkazish |
| POST | `/api/auth/login/` | Kirish (access + refresh token) |
| POST | `/api/auth/login/refresh/` | Token yangilash |
| POST | `/api/auth/change-password/` | Parolni o'zgartirish |
| GET | `/api/auth/user/` | Joriy foydalanuvchi ma'lumotlari |

### Hujjatlar

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/documents/` | Hujjatlar ro'yxati |
| POST | `/api/documents/` | Yangi hujjat yaratish |
| GET | `/api/documents/{id}/` | Hujjat tafsilotlari |
| GET | `/api/documents/{id}/files/` | Fayllar ro'yxati |
| POST | `/api/documents/{id}/files/` | Fayl yuklash |

### Xarid buyurtmalari

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/purchase-orders/` | Buyurtmalar ro'yxati |
| POST | `/api/purchase-orders/` | Yangi buyurtma |
| GET | `/api/purchase-orders/{id}/` | Buyurtma tafsilotlari |

### Yetkazib beruvchilar

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/suppliers/` | Yetkazib beruvchilar ro'yxati |
| GET | `/api/suppliers/{id}/` | Yetkazib beruvchi tafsilotlari |

### Ombor va Materiallar

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/materials/` | Materiallar ro'yxati |
| GET | `/api/warehouses/` | Omborxonalar ro'yxati |
| GET | `/api/inventory-items/` | Inventarizatsiya holati |

### Tashkilot

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/branches/` | Sho'ba bo'limlar |
| GET | `/api/construction-sites/` | Qurilish maydonchalari |

### Moliya

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/contracts/` | Shartnomalar ro'yxati |
| GET | `/api/contracts/{id}/` | Shartnoma tafsilotlari |
| GET | `/api/invoices/` | Hisob-fakturalar |
| POST | `/api/invoices/` | Yangi hisob-faktura |
| GET | `/api/invoices/{id}/` | Hisob-faktura tafsilotlari |
| GET | `/api/payments/` | To'lovlar ro'yxati |
| POST | `/api/invoices/{id}/payments/` | To'lov qilish |

### Ishlab chiqarish

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/production-requests/` | Zayavkalar ro'yxati |
| POST | `/api/production-requests/` | Yangi zayavka |
| GET | `/api/production-requests/{id}/` | Zayavka tafsilotlari |

### Murojaatlar (Ticket)

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/tickets/` | Murojaatlar ro'yxati |
| POST | `/api/tickets/` | Yangi murojaat |
| GET | `/api/tickets/{id}/` | Murojaat tafsilotlari |

### Manzillar

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/addresses/` | Manzillar ro'yxati |
| POST | `/api/addresses/` | Yangi manzil |
| GET | `/api/addresses/{id}/` | Manzil tafsilotlari |
| PUT/PATCH | `/api/addresses/{id}/` | Manzilni tahrirlash |
| DELETE | `/api/addresses/{id}/` | Manzilni o'chirish |

### Dashboard va Bildirishnomalar

| Metod | Endpoint | Tavsif |
|-------|----------|--------|
| GET | `/api/dashboard/` | Umumiy statistika |
| GET | `/api/notifications/` | Bildirishnomalar ro'yxati |
| POST | `/api/notifications/{id}/read/` | O'qilgan deb belgilash |
| POST | `/api/notifications/read-all/` | Hammasini o'qilgan deb belgilash |

---

## 🗄 Ma'lumotlar modeli

### Asosiy entitetlar

```
User
├── Branch (sho'ba bo'lim)
├── ConstructionSite (Qurilish maydonchasi)
│   └── ProductionRequest (Zayavka)
│   └── Ticket (Murojaat)
├── Warehouse (Omborxona)
│   └── InventoryItem (Inventarizatsiya)
│       └── StockMovement (Harakat)
├── Material (Material)
├── Document (Hujjat)
│   ├── DocumentFile (Fayl)
│   ├── Contract (Shartnoma)
│   └── Invoice (Hisob-faktura)
│       └── Payment (To'lov)
├── Supplier (Yetkazib beruvchi)
│   └── PurchaseOrder (Buyurtma)
│       └── PurchaseOrderItem
└── Notification (Bildirishnoma)

Address (Manzil) — mustaqil entitet
AuditLog — audit yorlig'i
```

---

## 🔐 Xavfsizlik

- **JWT autentifikatsiya** — access va refresh tokenlar
- **Role-based access** — admin va oddiy foydalanuvchi
- **CORS** — django-cors-headers orqali konfiguratsiya
- **API throttling** — DRF throttling sozlamalari
- **File upload limit** — 10MB max fayl hajmi
- **Audit logging** — barcha CRUD operatsiyalar yoziladi

---

## 📦 Loyiha tuzilishi

```
e-ombor/
├── backend/
│   ├── api/                    # Asosiy Django app
│   │   ├── admin.py            # Django admin konfiguratsiya
│   │   ├── models.py           # Ma'lumotlar modellar
│   │   ├── serializers.py      # DRF serializatorlar
│   │   ├── urls.py             # URL route'lar
│   │   └── views.py            # API Views
│   ├── e_ombor_backend/        # Project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py / asgi.py
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                    # Maxfiy sozlamalar (gitignore'da)
│   ├── db.sqlite3              # Ma'lumotlar bazasi
│   └── venv/                   # Virtual muhit
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── pages/              # Sahifalar
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
└── README.md
```

---

## 🔮 Keyingi bosqichlar

- [ ] **Dashboard va rol asosida UI** — boshqaruv paneli, role-based navigatsiya
- [ ] **Ombor / ta'minot moduli** — to'liq ombor xarakatlari, inventarizatsiya
- [ ] **Ob'ekt/loyiha kuzatuvi** — qurilish ob'yektlari va analytics
- [ ] **e-imzo integratsiyasi** — raqamli imzo bilan hujjatlarni tasdiqlash
- [ ] **1C integratsiyasi** — buxgalteriya tizimi bilan sinxronlash
- [ ] **Export/Import** — Excel, CSV formatlarida eksport
- [ ] **Multi-region** — bir nechta mintaqalar qo'llab-quvvatlash
- [ ] **Docker & CI/CD** — containerizatsiya va avtomatik deploy

---

## 📝 Rivojlantirish

### Backend testlar

```bash
cd backend
python manage.py test
```

### Django Admin panel

```bash
# Superuser yaratish
python manage.py createsuperuser

# Serverni ishga tushirish
python manage.py runserver
```

Admin panel: `http://localhost:3000/admin/`

---

## 📄 Litsenziya

E-Ombor — tashkilot ichki foydalanish uchun.
