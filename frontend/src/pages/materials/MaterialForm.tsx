import { useState } from "react";
import type { Material, MaterialPayload } from "../../types/material";

interface MaterialFormProps {
  initialMaterial?: Material;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: MaterialPayload) => void;
  onCancel: () => void;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

export function MaterialForm({ initialMaterial, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: MaterialFormProps) {
  const [values, setValues] = useState<MaterialPayload>(() => initialMaterial ? { name: initialMaterial.name, code: initialMaterial.code, unit: initialMaterial.unit, category: initialMaterial.category, description: initialMaterial.description } : { name: "", code: "", unit: "", category: "", description: "" });

  function updateField<Key extends keyof typeof values>(key: Key, value: (typeof values)[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(values);
  }

  return <form onSubmit={handleSubmit} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><Field label="Nomi"><input required value={values.name} onChange={(event) => updateField("name", event.target.value)} className={inputClassName} /></Field><Field label="Kodi"><input required value={values.code} onChange={(event) => updateField("code", event.target.value)} className={inputClassName} /></Field><Field label="O‘lchov birligi"><input required value={values.unit} onChange={(event) => updateField("unit", event.target.value)} className={inputClassName} /></Field><Field label="Kategoriya"><input required value={values.category} onChange={(event) => updateField("category", event.target.value)} className={inputClassName} /></Field></div><Field label="Tavsif"><textarea rows={3} value={values.description} onChange={(event) => updateField("description", event.target.value)} className={inputClassName} /></Field><div className="flex justify-end gap-2 pt-2"><button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button><button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Saqlanmoqda..." : submitLabel}</button></div></form>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium text-gray-700"><span>{label}</span>{children}</label>;
}
