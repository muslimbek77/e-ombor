"""
Ombor qoldig'i bilan ishlash: qulflash, yetarlilik, hujjat bo'yicha qabul.

Qoldiqni o'zgartiradigan hamma narsa `transaction.atomic()` ichida va
`select_for_update()` bilan qulflanadi.
"""

from decimal import Decimal

from .models import InventoryItem, PurchaseOrderItem, StockMovement


class InsufficientStockError(Exception):
    """Omborda yetarli qoldiq bo'lmaganda ko'tariladi."""


def lock_inventory_item(warehouse, material, create_if_missing=False):
    """InventoryItem ni satr darajasida qulflab qaytaradi (transaction ichida chaqirilsin)."""
    item = InventoryItem.objects.select_for_update().filter(warehouse=warehouse, material=material).first()
    if item is None and create_if_missing:
        InventoryItem.objects.get_or_create(warehouse=warehouse, material=material, defaults={"quantity": 0})
        item = InventoryItem.objects.select_for_update().get(warehouse=warehouse, material=material)
    return item


def ensure_sufficient_stock(item, warehouse, material, quantity):
    available = item.quantity if item else Decimal("0")
    if available < quantity:
        raise InsufficientStockError(
            f"{warehouse.name} omborida {material.name} yetarli emas "
            f"(mavjud: {available}, so'ralgan: {quantity})"
        )


class ReceiptError(Exception):
    """Qabul qilishni bajarib bo'lmadi (ombor tanlanmagan yoki begona)."""


def resolve_receipt_warehouse(document, warehouse):
    """
    Qabul qilinadigan omborni tekshiradi.

    Ombor taxmin qilinmaydi — filialda bitta ombor bo'lsa ham. Tovarni qabul
    qilayotgan omborchi u qayerga kirganini o'zi biladi va shuni ko'rsatadi;
    noto'g'ri omborga tushgan kirim esa keyin faqat teskari harakat bilan
    tuzatiladi (`StockMovement` o'chirilmaydi).
    """
    if warehouse is None:
        raise ReceiptError("Qabul qilinadigan ombor ko'rsatilishi shart")
    if warehouse.branch_id != document.branch_id:
        raise ReceiptError("Ombor hujjat filialiga tegishli emas")
    return warehouse


def receive_purchase_items(document, user, warehouse=None):
    """
    `delivering → received`: xarid qatorlarini ombor qoldig'iga kiritadi.

    Ilgari bu o'tish faqat statusni almashtirardi. Ya'ni zanjir yakunlangan,
    tovar omborda, lekin qoldiq eski — xaridlar bo'limi keyingi so'rov bo'yicha
    qaror qabul qilishda ko'radigan raqam zanjir natijasini aks ettirmasdi.

    Chaqiruvchi transaksiya ichida ishlaydi: kirim va status bir vaqtda
    yoziladi yoki umuman yozilmaydi.
    """
    items = list(
        PurchaseOrderItem.objects.filter(purchase_order__document=document)
        .select_related("material")
        .exclude(material__isnull=True)
    )
    if not items:
        # Xarid buyurtmasi yo'q yoki qatorlari bo'sh — hamma hujjat xarid
        # so'rovi emas. Bu xato emas, shunchaki kirim qiladigan narsa yo'q,
        # shuning uchun ombor ham so'ralmaydi.
        return []

    target = resolve_receipt_warehouse(document, warehouse)
    movements = []
    for item in items:
        inventory_item = lock_inventory_item(target, item.material, create_if_missing=True)
        inventory_item.quantity += item.quantity
        inventory_item.save(update_fields=["quantity", "updated_at"])
        movements.append(
            StockMovement.objects.create(
                warehouse=target,
                material=item.material,
                movement_type="IN",
                quantity=item.quantity,
                reference_doc=document,
                performed_by=user,
                notes=f"{document.doc_number} bo'yicha qabul qilindi",
            )
        )
    return movements
