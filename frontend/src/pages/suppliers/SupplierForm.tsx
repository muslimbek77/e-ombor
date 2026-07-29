import { useState } from "react";
import type { Supplier, SupplierPayload } from "../../types/supplier";

interface SupplierFormProps {
  initialSupplier?: Supplier;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: SupplierPayload) => void;
  onCancel: () => void;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

export function SupplierForm({ initialSupplier, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: SupplierFormProps) {
  const [values, setValues] = useState<SupplierPayload>(() => initialSupplier ? {
    name: initialSupplier.name, code: initialSupplier.code, contact_person: initialSupplier.contact_person, phone: initialSupplier.phone, email: initialSupplier.email, address: initialSupplier.address, is_active: initialSupplier.is_active,
  } : { name: "", code: "", contact_person: "", phone: "", email: "", address: "", is_active: true });

  function updateField<Key extends keyof SupplierPayload>(key: Key, value: SupplierPayload[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nomi"><input required value={values.name} onChange={(event) => updateField("name", event.target.value)} className={inputClassName} /></Field>
        <Field label="Kodi"><input required value={values.code} onChange={(event) => updateField("code", event.target.value)} className={inputClassName} /></Field>
        <Field label="Mas’ul shaxs"><input required value={values.contact_person} onChange={(event) => updateField("contact_person", event.target.value)} className={inputClassName} /></Field>
        <Field label="Telefon"><input required type="tel" value={values.phone} onChange={(event) => updateField("phone", event.target.value)} className={inputClassName} /></Field>
        <Field label="Email"><input required type="email" value={values.email} onChange={(event) => updateField("email", event.target.value)} className={inputClassName} /></Field>
        <label className="flex items-center gap-3 pt-7 text-sm font-medium text-gray-700"><input type="checkbox" checked={values.is_active} onChange={(event) => updateField("is_active", event.target.checked)} className="size-4 accent-green-600" /> Faol supplier</label>
      </div>
      <Field label="Manzil"><textarea required rows={3} value={values.address} onChange={(event) => updateField("address", event.target.value)} className={inputClassName} /></Field>
      <div className="flex justify-end gap-2 pt-2"><button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button><button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Saqlanmoqda..." : submitLabel}</button></div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium text-gray-700"><span>{label}</span>{children}</label>;
}
