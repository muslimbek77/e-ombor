import { useState } from "react";
import type { Address, AddressPayload } from "../../types/address";

interface AddressFormProps {
  initialAddress?: Address;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: AddressPayload) => void;
  onCancel: () => void;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

export function AddressForm({ initialAddress, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: AddressFormProps) {
  const [values, setValues] = useState<AddressPayload>(() => initialAddress ? { city: initialAddress.city, district: initialAddress.district, street: initialAddress.street, building: initialAddress.building } : { city: "", district: "", street: "", building: "" });

  function updateField<Key extends keyof AddressPayload>(key: Key, value: AddressPayload[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Shahar"><input required value={values.city} onChange={(event) => updateField("city", event.target.value)} className={inputClassName} /></Field>
        <Field label="Tuman"><input value={values.district} onChange={(event) => updateField("district", event.target.value)} className={inputClassName} /></Field>
        <Field label="Ko'cha"><input value={values.street} onChange={(event) => updateField("street", event.target.value)} className={inputClassName} /></Field>
        <Field label="Bino"><input value={values.building} onChange={(event) => updateField("building", event.target.value)} className={inputClassName} /></Field>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Saqlanmoqda..." : submitLabel}</button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5 text-sm font-medium text-gray-700">
      <span>{label}</span>
      {children}
    </label>
  );
}
