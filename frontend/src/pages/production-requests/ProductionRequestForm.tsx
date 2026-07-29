import { useState } from "react";
import type { ProductionRequest, ProductionRequestCreatePayload, ProductionRequestStatus, ProductionRequestUpdatePayload } from "../../types/productionRequest";
import { useSites } from "../../hooks/useObjects";
import { STATUS_OPTIONS } from "./productionRequestUtils";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface ProductionRequestFormValues {
  title: string;
  description: string;
  site: string;
  status: ProductionRequestStatus;
}

function getFormValues(request?: ProductionRequest): ProductionRequestFormValues {
  if (!request) return { title: "", description: "", site: "", status: "pending" };
  return { title: request.title, description: request.description, site: String(request.site), status: request.status };
}

interface ProductionRequestFormProps {
  initialRequest?: ProductionRequest;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: ProductionRequestCreatePayload | ProductionRequestUpdatePayload) => void;
  onCancel: () => void;
}

export function ProductionRequestForm({ initialRequest, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: ProductionRequestFormProps) {
  const [values, setValues] = useState<ProductionRequestFormValues>(() => getFormValues(initialRequest));
  const { data: sites = [], isPending: isSitesPending } = useSites();

  function updateField<Key extends keyof ProductionRequestFormValues>(key: Key, value: ProductionRequestFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const basePayload: ProductionRequestCreatePayload = {
      title: values.title,
      description: values.description,
      site: Number(values.site),
    };

    if (!initialRequest) {
      onSubmit(basePayload);
      return;
    }

    onSubmit({ ...basePayload, status: values.status } satisfies ProductionRequestUpdatePayload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Sarlavha" className="sm:col-span-2">
          <input required value={values.title} onChange={(event) => updateField("title", event.target.value)} className={inputClassName} placeholder="Masalan: Beton bloklar uchun zayavka" />
        </Field>
        <Field label="Obyekt">
          <select required disabled={isSitesPending} value={values.site} onChange={(event) => updateField("site", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select>
        </Field>
        {initialRequest && (
          <Field label="Holati">
            <select value={values.status} onChange={(event) => updateField("status", event.target.value as ProductionRequestStatus)} className={inputClassName}>
              {STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </Field>
        )}
      </div>
      <Field label="Tavsif">
        <textarea rows={3} value={values.description} onChange={(event) => updateField("description", event.target.value)} className={inputClassName} placeholder="Zayavka tafsilotlari..." />
      </Field>
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
