import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useDocuments } from "../../hooks/useDocuments";
import { useMaterials } from "../../hooks/useMaterials";
import { useSuppliers } from "../../hooks/useSuppliers";
import type { PurchaseOrder, PurchaseOrderCreatePayload, PurchaseOrderUpdatePayload } from "../../types/purchaseOrder";

interface PurchaseOrderItemFormValue {
  material: string;
  quantity: string;
  unit_price: string;
}

interface PurchaseOrderFormProps {
  initialPurchaseOrder?: PurchaseOrder;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: PurchaseOrderCreatePayload | PurchaseOrderUpdatePayload) => void;
  onCancel: () => void;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";
const emptyItem: PurchaseOrderItemFormValue = { material: "", quantity: "", unit_price: "" };

export function PurchaseOrderForm({ initialPurchaseOrder, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: PurchaseOrderFormProps) {
  const isEditing = Boolean(initialPurchaseOrder);
  const { data: documents, isLoading: isDocumentsLoading } = useDocuments();
  const { data: suppliers, isLoading: isSuppliersLoading } = useSuppliers();
  const { data: materials, isLoading: isMaterialsLoading } = useMaterials();
  const [document, setDocument] = useState(() => (initialPurchaseOrder ? String(initialPurchaseOrder.document) : ""));
  const [supplier, setSupplier] = useState(() => (initialPurchaseOrder?.supplier ? String(initialPurchaseOrder.supplier) : ""));
  const [items, setItems] = useState<PurchaseOrderItemFormValue[]>(() => (initialPurchaseOrder?.items.length ? initialPurchaseOrder.items.map((item) => ({ material: String(item.material), quantity: item.quantity, unit_price: item.unit_price })) : [{ ...emptyItem }]));

  function updateItem(index: number, key: keyof PurchaseOrderItemFormValue, value: string) {
    setItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item)));
  }

  function addItem() {
    setItems((current) => [...current, { ...emptyItem }]);
  }

  function removeItem(index: number) {
    setItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payloadItems = items.map((item) => ({ material: Number(item.material), quantity: Number(item.quantity), unit_price: Number(item.unit_price) }));
    if (isEditing) onSubmit({ supplier: supplier ? Number(supplier) : null, items: payloadItems });
    else onSubmit({ document: Number(document), supplier: supplier ? Number(supplier) : null, items: payloadItems });
  }

  return <form onSubmit={handleSubmit} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2">{!isEditing && <Field label="Hujjat"><select required disabled={isDocumentsLoading} value={document} onChange={(event) => setDocument(event.target.value)} className={inputClassName}><option value="" disabled>{isDocumentsLoading ? "Yuklanmoqda..." : "Hujjatni tanlang"}</option>{documents?.map((doc) => <option key={doc.id} value={doc.id}>{doc.doc_number} — {doc.title}</option>)}</select></Field>}<Field label="Yetkazib beruvchi"><select disabled={isSuppliersLoading} value={supplier} onChange={(event) => setSupplier(event.target.value)} className={inputClassName}><option value="">Tanlanmagan</option>{suppliers?.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field></div><div className="space-y-3"><div className="flex items-center justify-between"><h3 className="text-sm font-bold text-gray-900">Mahsulotlar</h3><button type="button" onClick={addItem} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-1.5 text-sm font-semibold text-gray-700 hover:bg-gray-50"><Plus size={15} /> Qator qo‘shish</button></div><div className="space-y-3">{items.map((item, index) => { const totalPrice = (Number(item.quantity) || 0) * (Number(item.unit_price) || 0); return <div key={index} className="grid grid-cols-1 gap-3 rounded-xl border border-gray-100 p-3 sm:grid-cols-[2fr_1fr_1fr_1fr_auto]"><Field label="Material"><select required disabled={isMaterialsLoading} value={item.material} onChange={(event) => updateItem(index, "material", event.target.value)} className={inputClassName}><option value="" disabled>{isMaterialsLoading ? "Yuklanmoqda..." : "Materialni tanlang"}</option>{materials?.map((material) => <option key={material.id} value={material.id}>{material.name}</option>)}</select></Field><Field label="Miqdor"><input required type="number" min="0" step="any" value={item.quantity} onChange={(event) => updateItem(index, "quantity", event.target.value)} className={inputClassName} /></Field><Field label="Narx"><input required type="number" min="0" step="any" value={item.unit_price} onChange={(event) => updateItem(index, "unit_price", event.target.value)} className={inputClassName} /></Field><Field label="Jami"><input readOnly disabled value={totalPrice} className={`${inputClassName} bg-gray-50 text-gray-500`} /></Field><div className="flex items-end">{items.length > 1 && <button type="button" onClick={() => removeItem(index)} aria-label="Qatorni o‘chirish" className="rounded-xl p-2 text-red-600 hover:bg-red-50"><Trash2 size={16} /></button>}</div></div>; })}</div></div><div className="flex justify-end gap-2 pt-2"><button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button><button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Saqlanmoqda..." : submitLabel}</button></div></form>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium text-gray-700"><span>{label}</span>{children}</label>;
}
