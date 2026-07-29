import { useState } from "react";
import type { PaymentCreatePayload } from "../../types/payment";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface PaymentFormProps {
  isSubmitting?: boolean;
  onSubmit: (payload: PaymentCreatePayload) => void;
  onCancel: () => void;
}

export function PaymentForm({ isSubmitting, onSubmit, onCancel }: PaymentFormProps) {
  const [amount, setAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [referenceNumber, setReferenceNumber] = useState("");
  const [notes, setNotes] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({ amount: Number(amount), payment_method: paymentMethod, reference_number: referenceNumber, notes });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Summa">
          <input required type="number" min="0" step="any" value={amount} onChange={(event) => setAmount(event.target.value)} className={inputClassName} />
        </Field>
        <Field label="To'lov usuli">
          <input value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)} placeholder="Naqd, bank o'tkazmasi..." className={inputClassName} />
        </Field>
        <Field label="Referens raqami" className="sm:col-span-2">
          <input value={referenceNumber} onChange={(event) => setReferenceNumber(event.target.value)} className={inputClassName} />
        </Field>
      </div>
      <Field label="Izoh">
        <textarea rows={2} value={notes} onChange={(event) => setNotes(event.target.value)} className={inputClassName} />
      </Field>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : "To'lovni qo'shish"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
