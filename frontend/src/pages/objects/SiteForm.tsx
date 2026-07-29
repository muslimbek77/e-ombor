import { useState } from "react";
import type { Site, SitePayload, SiteStatus } from "../../types/site";
import { useBranches } from "../../hooks/useBranches";
import { useProrabs } from "../../hooks/useUsers";

const STATUS_OPTIONS: { value: SiteStatus; label: string }[] = [
  { value: "active", label: "Faol" },
  { value: "paused", label: "To'xtatilgan" },
  { value: "completed", label: "Tugallangan" },
];

interface SiteFormProps {
  initialSite?: Site;
  submitLabel: string;
  isSubmitting?: boolean;
  onSubmit: (payload: SitePayload) => void;
  onCancel?: () => void;
}

type FormValues = Omit<SitePayload, "branch" | "prorab"> & {
  branch: string;
  prorab: string;
};

const EMPTY_VALUES: FormValues = {
  name: "",
  code: "",
  branch: "",
  address: "",
  status: "active",
  budget: "",
  prorab: "",
};

function getFormValues(site?: Site): FormValues {
  if (!site) return EMPTY_VALUES;

  return {
    name: site.name,
    code: site.code,
    branch: String(site.branch),
    address: site.address,
    status: site.status,
    budget: site.budget,
    prorab: String(site.prorab),
  };
}

export function SiteForm({ initialSite, submitLabel, isSubmitting, onSubmit, onCancel }: SiteFormProps) {
  const [values, setValues] = useState<FormValues>(() => getFormValues(initialSite));
  const { data: branches = [], isPending: isBranchesPending } = useBranches();
  const { data: prorabs, isPending: isProrabsPending, isError: isProrabsError } = useProrabs();

  function updateField<Key extends keyof FormValues>(key: Key, value: FormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    onSubmit({
      ...values,
      branch: Number(values.branch),
      prorab: Number(values.prorab),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Nomi">
          <input required value={values.name} onChange={(event) => updateField("name", event.target.value)} className={inputClassName} />
        </FormField>
        <FormField label="Kodi">
          <input required value={values.code} onChange={(event) => updateField("code", event.target.value)} className={inputClassName} />
        </FormField>
        <FormField label="Filial">
          <select required disabled={isBranchesPending} value={values.branch} onChange={(event) => updateField("branch", event.target.value)} className={inputClassName}>
            <option value="" disabled>{isBranchesPending ? "Yuklanmoqda..." : "Filialni tanlang"}</option>
            {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
          </select>
        </FormField>
        <FormField label="Prorab">
          {isProrabsError ? (
            <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
              Prorablar ro‘yxatini yuklashga ruxsat yo‘q{initialSite ? ` — joriy prorab: ${initialSite.prorab_name}` : ""}.
            </p>
          ) : (
            <select required disabled={isProrabsPending} value={values.prorab} onChange={(event) => updateField("prorab", event.target.value)} className={inputClassName}>
              <option value="" disabled>{isProrabsPending ? "Yuklanmoqda..." : "Prorabni tanlang"}</option>
              {prorabs?.map((prorab) => <option key={prorab.id} value={prorab.id}>{prorab.full_name}</option>)}
            </select>
          )}
        </FormField>
        <FormField label="Holati">
          <select value={values.status} onChange={(event) => updateField("status", event.target.value)} className={inputClassName}>
            {STATUS_OPTIONS.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
          </select>
        </FormField>
        <FormField label="Byudjet">
          <input required inputMode="decimal" value={values.budget} onChange={(event) => updateField("budget", event.target.value)} className={inputClassName} />
        </FormField>
      </div>
      <FormField label="Manzil">
        <textarea required rows={3} value={values.address} onChange={(event) => updateField("address", event.target.value)} className={inputClassName} />
      </FormField>
      <div className="flex justify-end gap-2 pt-2">
        {onCancel && <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>}
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block space-y-1.5 text-sm font-medium text-gray-700"><span>{label}</span>{children}</label>;
}

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";
