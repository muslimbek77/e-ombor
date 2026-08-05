import { useState } from "react";
import { useDocuments } from "../../hooks/useDocuments";
import { useSuppliers } from "../../hooks/useSuppliers";
import { useContracts } from "../../hooks/useContracts";
import type { Contract, ContractPayload } from "../../types/shartnoma";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface ContractFormValues {
  document: string;
  supplier: string;
  contract_number: string;
  signed_date: string;
  start_date: string;
  end_date: string;
  total_amount: string;
  description: string;
}

function getFormValues(contract?: Contract): ContractFormValues {
  if (!contract) {
    return { document: "", supplier: "", contract_number: "", signed_date: "", start_date: "", end_date: "", total_amount: "", description: "" };
  }
  return {
    document: String(contract.document),
    supplier: contract.supplier ? String(contract.supplier) : "",
    contract_number: contract.contract_number,
    signed_date: contract.signed_date ?? "",
    start_date: contract.start_date ?? "",
    end_date: contract.end_date ?? "",
    total_amount: contract.total_amount,
    description: contract.description,
  };
}

interface ContractFormProps {
  initialContract?: Contract;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: ContractPayload) => void;
  onCancel: () => void;
}

export function ContractForm({ initialContract, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: ContractFormProps) {
  const isEditing = Boolean(initialContract);
  const [values, setValues] = useState<ContractFormValues>(() => getFormValues(initialContract));
  const { data: documents = [], isPending: isDocumentsPending } = useDocuments();
  const { data: suppliers = [], isPending: isSuppliersPending } = useSuppliers();
  const { data: contracts = [] } = useContracts();

  const usedDocumentIds = new Set(contracts.map((contract) => contract.document));
  const availableDocuments = documents.filter((doc) => doc.doc_type === "contract" && !usedDocumentIds.has(doc.id));

  function updateField<Key extends keyof ContractFormValues>(key: Key, value: ContractFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload: ContractPayload = {
      document: Number(values.document),
      supplier: values.supplier ? Number(values.supplier) : null,
      contract_number: values.contract_number,
      signed_date: values.signed_date || null,
      start_date: values.start_date || null,
      end_date: values.end_date || null,
      total_amount: Number(values.total_amount),
      description: values.description,
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
        <Field label="Yetkazib beruvchi">
          <select disabled={isSuppliersPending} value={values.supplier} onChange={(event) => updateField("supplier", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}
          </select>
        </Field>
        <Field label="Shartnoma raqami">
          <input required value={values.contract_number} onChange={(event) => updateField("contract_number", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Imzolangan sana">
          <input type="date" value={values.signed_date} onChange={(event) => updateField("signed_date", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Umumiy summa">
          <input required type="number" min="0" step="any" value={values.total_amount} onChange={(event) => updateField("total_amount", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Boshlanish sanasi">
          <input type="date" value={values.start_date} onChange={(event) => updateField("start_date", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Tugash sanasi">
          <input type="date" value={values.end_date} onChange={(event) => updateField("end_date", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Izoh" className="sm:col-span-2">
          <textarea rows={3} value={values.description} onChange={(event) => updateField("description", event.target.value)} className={inputClassName} />
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
