import { useState } from "react";
import { useSites } from "../../hooks/useObjects";
import type { AppDocument, DocType, DocumentCreatePayload, DocumentUpdatePayload } from "../../types/document";
import { DOC_TYPE_OPTIONS } from "./documentUtils";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface DocumentFormValues {
  doc_type: DocType;
  title: string;
  description: string;
  site: string;
  total_amount: string;
  notes: string;
}

function getFormValues(document?: AppDocument): DocumentFormValues {
  if (!document) {
    return { doc_type: "purchase_request", title: "", description: "", site: "", total_amount: "0", notes: "" };
  }
  return {
    doc_type: document.doc_type,
    title: document.title,
    description: document.description,
    site: document.site ? String(document.site) : "",
    total_amount: document.total_amount,
    notes: document.notes,
  };
}

interface DocumentFormProps {
  initialDocument?: AppDocument;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: DocumentCreatePayload | DocumentUpdatePayload) => void;
  onCancel: () => void;
}

export function DocumentForm({ initialDocument, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: DocumentFormProps) {
  const isEditing = Boolean(initialDocument);
  const [values, setValues] = useState<DocumentFormValues>(() => getFormValues(initialDocument));
  const { data: sites = [], isPending: isSitesPending } = useSites();

  function updateField<Key extends keyof DocumentFormValues>(key: Key, value: DocumentFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload: DocumentCreatePayload | DocumentUpdatePayload = {
      doc_type: values.doc_type,
      title: values.title,
      description: values.description,
      site: values.site ? Number(values.site) : null,
      total_amount: Number(values.total_amount),
      notes: values.notes,
    };

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Hujjat turi">
          <select disabled={isEditing} required value={values.doc_type} onChange={(event) => updateField("doc_type", event.target.value as DocType)} className={`${inputClassName} disabled:bg-gray-50 disabled:text-gray-500`}>
            {DOC_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </Field>
        <Field label="Obyekt (ixtiyoriy)">
          <select disabled={isSitesPending} value={values.site} onChange={(event) => updateField("site", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select>
        </Field>
        <Field label="Sarlavha" className="sm:col-span-2">
          <input required value={values.title} onChange={(event) => updateField("title", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Umumiy summa">
          <input required type="number" min="0" step="any" value={values.total_amount} onChange={(event) => updateField("total_amount", event.target.value)} className={inputClassName} />
        </Field>
      </div>
      <Field label="Tavsif">
        <textarea rows={2} value={values.description} onChange={(event) => updateField("description", event.target.value)} className={inputClassName} />
      </Field>
      <Field label="Izoh">
        <textarea rows={2} value={values.notes} onChange={(event) => updateField("notes", event.target.value)} className={inputClassName} />
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
