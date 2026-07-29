import { useState } from "react";
import { useMaterials } from "../../hooks/useMaterials";
import { useWarehouses } from "../../hooks/useWarehouses";
import type { InventoryItemPayload } from "../../types/inventory";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface InventoryFormValues {
  warehouse: string;
  material: string;
  quantity: string;
  min_quantity: string;
}

interface InventoryFormProps {
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: InventoryItemPayload) => void;
  onCancel: () => void;
}

export function InventoryForm({ submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: InventoryFormProps) {
  const [values, setValues] = useState<InventoryFormValues>({ warehouse: "", material: "", quantity: "0", min_quantity: "0" });
  const { data: warehouses = [], isPending: isWarehousesPending } = useWarehouses();
  const { data: materials = [], isPending: isMaterialsPending } = useMaterials();

  function updateField<Key extends keyof InventoryFormValues>(key: Key, value: InventoryFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload: InventoryItemPayload = {
      warehouse: Number(values.warehouse),
      material: Number(values.material),
      quantity: Number(values.quantity),
      min_quantity: Number(values.min_quantity),
    };

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Ombor">
          <select required disabled={isWarehousesPending} value={values.warehouse} onChange={(event) => updateField("warehouse", event.target.value)} className={inputClassName}>
            <option value="" disabled>{isWarehousesPending ? "Yuklanmoqda..." : "Omborni tanlang"}</option>
            {warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
          </select>
        </Field>
        <Field label="Material">
          <select required disabled={isMaterialsPending} value={values.material} onChange={(event) => updateField("material", event.target.value)} className={inputClassName}>
            <option value="" disabled>{isMaterialsPending ? "Yuklanmoqda..." : "Materialni tanlang"}</option>
            {materials.map((material) => <option key={material.id} value={material.id}>{material.name} ({material.code})</option>)}
          </select>
        </Field>
        <Field label="Boshlang'ich miqdor">
          <input required type="number" min="0" step="any" value={values.quantity} onChange={(event) => updateField("quantity", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Minimal zaxira">
          <input required type="number" min="0" step="any" value={values.min_quantity} onChange={(event) => updateField("min_quantity", event.target.value)} className={inputClassName} />
        </Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
