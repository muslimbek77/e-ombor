import { useState } from "react";
import { useWarehouses } from "../../hooks/useWarehouses";
import type { InventoryItem } from "../../types/inventory";
import type { MovementType, StockMovementCreatePayload } from "../../types/stockMovement";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

const MOVEMENT_TYPES: { value: MovementType; label: string }[] = [
  { value: "IN", label: "Kirim" },
  { value: "OUT", label: "Chiqim" },
  { value: "TRANSFER", label: "Ko'chirish" },
];

interface MovementFormProps {
  item: InventoryItem;
  isSubmitting?: boolean;
  onSubmit: (payload: StockMovementCreatePayload) => void;
  onCancel: () => void;
}

export function MovementForm({ item, isSubmitting, onSubmit, onCancel }: MovementFormProps) {
  const [movementType, setMovementType] = useState<MovementType>("IN");
  const [targetWarehouse, setTargetWarehouse] = useState("");
  const [quantity, setQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const { data: warehouses = [] } = useWarehouses();

  const otherWarehouses = warehouses.filter((warehouse) => warehouse.id !== item.warehouse);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      warehouse: item.warehouse,
      material: item.material,
      movement_type: movementType,
      quantity: Number(quantity),
      target_warehouse: movementType === "TRANSFER" ? Number(targetWarehouse) : undefined,
      notes,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Harakat turi">
          <select value={movementType} onChange={(event) => setMovementType(event.target.value as MovementType)} className={inputClassName}>
            {MOVEMENT_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
        </Field>
        <Field label="Miqdor">
          <input required type="number" min="0" step="any" value={quantity} onChange={(event) => setQuantity(event.target.value)} className={inputClassName} />
        </Field>
        {movementType === "TRANSFER" && (
          <Field label="Maqsad ombor" className="sm:col-span-2">
            <select required value={targetWarehouse} onChange={(event) => setTargetWarehouse(event.target.value)} className={inputClassName}>
              <option value="" disabled>Omborni tanlang</option>
              {otherWarehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
            </select>
          </Field>
        )}
        <Field label="Izoh" className="sm:col-span-2">
          <textarea rows={2} value={notes} onChange={(event) => setNotes(event.target.value)} className={inputClassName} />
        </Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
