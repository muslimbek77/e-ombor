import { useState } from "react";
import { useDocuments } from "../../hooks/useDocuments";
import { useContracts } from "../../hooks/useContracts";
import { useInvoices } from "../../hooks/useInvoices";
import type { Invoice, InvoiceCreatePayload, InvoiceUpdatePayload } from "../../types/invoice";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface InvoiceFormValues {
  document: string;
  contract: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  total_amount: string;
}

function getFormValues(invoice?: Invoice): InvoiceFormValues {
  if (!invoice) {
    return { document: "", contract: "", invoice_number: "", invoice_date: "", due_date: "", total_amount: "" };
  }
  return {
    document: String(invoice.document),
    contract: invoice.contract ? String(invoice.contract) : "",
    invoice_number: invoice.invoice_number,
    invoice_date: invoice.invoice_date,
    due_date: invoice.due_date ?? "",
    total_amount: invoice.total_amount,
  };
}

interface InvoiceFormProps {
  initialInvoice?: Invoice;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: InvoiceCreatePayload | InvoiceUpdatePayload) => void;
  onCancel: () => void;
}

export function InvoiceForm({ initialInvoice, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: InvoiceFormProps) {
  const isEditing = Boolean(initialInvoice);
  const [values, setValues] = useState<InvoiceFormValues>(() => getFormValues(initialInvoice));
  const { data: documents = [], isPending: isDocumentsPending } = useDocuments();
  const { data: contracts = [], isPending: isContractsPending } = useContracts();
  const { data: invoices = [] } = useInvoices();

  const usedDocumentIds = new Set(invoices.map((invoice) => invoice.document));
  const availableDocuments = documents.filter((doc) => doc.doc_type === "invoice" && !usedDocumentIds.has(doc.id));

  function updateField<Key extends keyof InvoiceFormValues>(key: Key, value: InvoiceFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload: InvoiceCreatePayload | InvoiceUpdatePayload = {
      document: Number(values.document),
      contract: values.contract ? Number(values.contract) : null,
      invoice_number: values.invoice_number,
      invoice_date: values.invoice_date,
      due_date: values.due_date || null,
      total_amount: Number(values.total_amount),
    };

    onSubmit(payload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {!isEditing && (
          <Field label="Hujjat" className="sm:col-span-2">
            <select required disabled={isDocumentsPending} value={values.document} onChange={(event) => updateField("document", event.target.value)} className={inputClassName}>
              <option value="" disabled>{isDocumentsPending ? "Yuklanmoqda..." : "Hujjatni tanlang"}</option>
              {availableDocuments.map((doc) => <option key={doc.id} value={doc.id}>{doc.doc_number} — {doc.title}</option>)}
            </select>
          </Field>
        )}
        <Field label="Shartnoma (ixtiyoriy)">
          <select disabled={isContractsPending} value={values.contract} onChange={(event) => updateField("contract", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {contracts.map((contract) => <option key={contract.id} value={contract.id}>{contract.contract_number || contract.document_doc_number}</option>)}
          </select>
        </Field>
        <Field label="Invoice raqami">
          <input required value={values.invoice_number} onChange={(event) => updateField("invoice_number", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Sana">
          <input required type="date" value={values.invoice_date} onChange={(event) => updateField("invoice_date", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="To'lov muddati (ixtiyoriy)">
          <input type="date" value={values.due_date} onChange={(event) => updateField("due_date", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Umumiy summa">
          <input required type="number" min="0" step="any" value={values.total_amount} onChange={(event) => updateField("total_amount", event.target.value)} className={inputClassName} />
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
