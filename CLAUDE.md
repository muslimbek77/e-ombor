# CLAUDE.md

Bu fayl Claude Code uchun — loyihada tez mo'ljal olish uchun. Frontendga xos
tafsilotlar alohida: `frontend/CLAUDE.md`.

## Nima bu

E-Ombor — qurilish tashkilotlari uchun ombor, hujjat aylanishi va moliya
platformasi. Django REST (backend) + React/TypeScript (frontend). Interfeys va
kod izohlari o'zbekcha.

## Komandalar

```bash
# Backend
cd backend && source venv/bin/activate
python manage.py test api          # 159 test — o'zgarishdan keyin shu yuritiladi
python manage.py migrate
python manage.py seed_demo_data    # demo to'plam + demo loginlar
python manage.py runserver 0.0.0.0:3000

# Frontend
cd frontend
npx tsc --noEmit                   # typecheck
npm run lint                       # 3 ta `react-refresh` xatosi main'da ham bor
npm run dev
```

## Muhim fayllar

| Nima kerak bo'lsa | Qayerda |
|---|---|
| Tasdiqlash zanjiri, tahrirlanadigan holatlar, SoD to'plami | `backend/api/workflow.py` |
| Nazorat rolining global yozish taqiqi | `backend/api/permissions.py` + `settings.py: DEFAULT_PERMISSION_CLASSES` |
| Rol to'plamlari | `backend/api/roles.py` |
| Ko'rish doirasi (`branch_scope`) | `backend/api/scope.py` |
| Endpointlar | `backend/api/views/` (domen bo'yicha) |
| Modellar | `backend/api/models.py` |
| Frontend rol nusxasi (faqat UI uchun) | `frontend/src/lib/permissions.ts` |
| Tizim mantiqining to'liq bayoni | `docs/TIZIM.md` |

## Qoidalar

**Zanjir faqat `workflow.py` da.** Ilgari u `views/` va `serializers.py` da
takrorlangan edi va ajralib qolishi mumkin edi — natijada foydalanuvchiga
bosilganda 403 beradigan tugma ko'rinardi. Endi ikkalasi ham shu fayldan
o'qiydi. Yangi bosqich qo'shilsa: `workflow.py` + `models.py: Document.STATUSES`
+ migration + frontend `types/document.ts` va `documentUtils.ts`.

**Ko'rish va yozish alohida.** `GLOBAL_SCOPE_ROLES` (`roles.py`) faqat
`branch_scope()` ga ta'sir qiladi — ya'ni kim nimani ko'radi. Yozish huquqi
o'sha yerdagi alohida to'plamlar (`PAYMENT_ROLES`, `STOCK_MOVEMENT_ROLES` va
h.k.) bilan tekshiriladi. Ikkalasini aralashtirmaslik kerak.

**Frontenddagi `permissions.ts` — himoya emas.** U backend to'plamlarining
nusxasi, maqsadi — bosilganda 403 beradigan tugmani ko'rsatmaslik. Rol
to'plami o'zgarsa ikkala joy ham yangilanadi.

**Nazorat roli (`anticorruption`) faqat o'qiydi.** Taqiq global —
`DEFAULT_PERMISSION_CLASSES` da. DRF'da view o'z `permission_classes` ini
e'lon qilsa default butunlay almashadi, shuning uchun qo'shimcha ruxsat sinfi
kerak bo'lsa u `views.DEFAULT_PERMISSIONS` USTIGA qo'shiladi, o'rniga emas.
Istisno kerak bo'lsa view'ga `control_role_may_write = True` yoziladi. Buni
`tests_control_role.py` urls.py bo'yicha tekshiradi.

**Hujjat `created`, `revision` va `rejected` dan tashqarida muzlaydi.**
Tahrirlash va o'chirish 409 qaytaradi — admin ham istisno emas. Xuddi shu
`PurchaseOrder` qatorlariga tegishli. Holatlar ro'yxati
`workflow.py: EDITABLE_STATUSES`. Muzlatish izohga (`DocumentComment`) va
fayl biriktirishga tegishli emas: aynan muzlagan hujjat haqida gaplashish
kerak bo'ladi.

**`return` — `reject` emas.** Har bir tasdiqlash bosqichida `return` amali bor:
hujjat `revision` ga tushadi, tuzatiladi va `submit` bilan zanjirni
arxitekturadan qaytadan boshlaydi. Qaytadan boshlanishi ataylab — summa
o'zgargan bo'lsa oldingi tasdiqlar boshqa hujjatga tegishli bo'lib qoladi.
`reject` va `return` da izoh majburiy (`workflow.py:
COMMENT_REQUIRED_ACTIONS`).

**Qabul qoldiqni o'zgartiradi.** `delivering → received` (`advance`) hujjatning
xarid qatorlarini omborga kirim qiladi (`stock.py: receive_purchase_items`) —
status va `StockMovement` bitta transaksiyada. Qatorlari bor hujjatda so'rovdagi
`warehouse` majburiy va taxmin qilinmaydi (filialda bitta ombor bo'lsa ham):
xato kirim keyin faqat teskari harakat bilan tuzatiladi. Qatorsiz hujjatda
faqat status o'zgaradi.

**Ombor harakati o'chirilmaydi.** `stock-movements/` da tafsilot endpointi
ataylab yo'q. Xato kiritilgan harakat teskari harakat bilan tuzatiladi.

**Testlar kutilgan xulqni tasdiqlaydi.** Yiqilgan test — tuzatilishi kerak
bo'lgan xato, testni moslashtirish emas.
