import { useState } from "react";
import type { InventoryAdjustmentPayload, InventoryItem } from "../../types/inventory";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface AdjustStockFormProps {
  item: InventoryItem;
  isSubmitting?: boolean;
  onSubmit: (payload: InventoryAdjustmentPayload) => void;
  onCancel: () => void;
}

export function AdjustStockForm({ item, isSubmitting, onSubmit, onCancel }: AdjustStockFormProps) {
  const [delta, setDelta] = useState("0");
  const [minQuantity, setMinQuantity] = useState(item.min_quantity);
  const [notes, setNotes] = useState("");

  const numericDelta = Number(delta) || 0;
  const projectedQuantity = Number(item.quantity) + numericDelta;

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      quantity_delta: numericDelta,
      min_quantity: Number(minQuantity),
      notes,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Miqdor o'zgarishi (+/-)">
          <input required type="number" step="any" value={delta} onChange={(event) => setDelta(event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Minimal zaxira">
          <input required type="number" min="0" step="any" value={minQuantity} onChange={(event) => setMinQuantity(event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Izoh" className="sm:col-span-2">
          <textarea rows={2} value={notes} onChange={(event) => setNotes(event.target.value)} className={inputClassName} />
        </Field>
      </div>
      <p className="text-sm text-gray-500">Yangi miqdor: <span className={`font-semibold ${projectedQuantity < 0 ? "text-red-600" : "text-gray-900"}`}>{projectedQuantity}</span></p>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting || projectedQuantity < 0} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
