import { useState } from "react";
import { useBranches } from "../../hooks/useBranches";
import type { Warehouse, WarehousePayload } from "../../types/warehouse";

interface WarehouseFormProps {
  initialWarehouse?: Warehouse;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: WarehousePayload) => void;
  onCancel: () => void;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

export function WarehouseForm({ initialWarehouse, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: WarehouseFormProps) {
  const { data: branches, isLoading: isBranchesLoading } = useBranches();
  const [values, setValues] = useState<Omit<WarehousePayload, "branch"> & { branch: string }>(() => initialWarehouse ? { name: initialWarehouse.name, code: initialWarehouse.code, branch: String(initialWarehouse.branch), address: initialWarehouse.address, min_stock_alert: initialWarehouse.min_stock_alert } : { name: "", code: "", branch: "", address: "", min_stock_alert: true });

  function updateField<Key extends keyof typeof values>(key: Key, value: (typeof values)[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({ ...values, branch: Number(values.branch) });
  }

  return <form onSubmit={handleSubmit} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><Field label="Nomi"><input required value={values.name} onChange={(event) => updateField("name", event.target.value)} className={inputClassName} /></Field><Field label="Kodi"><input required value={values.code} onChange={(event) => updateField("code", event.target.value)} className={inputClassName} /></Field><Field label="Filial"><select required disabled={isBranchesLoading} value={values.branch} onChange={(event) => updateField("branch", event.target.value)} className={inputClassName}><option value="" disabled>{isBranchesLoading ? "Yuklanmoqda..." : "Filialni tanlang"}</option>{branches?.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></Field><label className="flex items-center gap-3 pt-7 text-sm font-medium text-gray-700"><input type="checkbox" checked={values.min_stock_alert} onChange={(event) => updateField("min_stock_alert", event.target.checked)} className="size-4 accent-green-600" /> Minimal zaxira ogohlantirishi</label></div><Field label="Manzil"><textarea required rows={3} value={values.address} onChange={(event) => updateField("address", event.target.value)} className={inputClassName} /></Field><div className="flex justify-end gap-2 pt-2"><button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button><button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Saqlanmoqda..." : submitLabel}</button></div></form>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium text-gray-700"><span>{label}</span>{children}</label>;
}
