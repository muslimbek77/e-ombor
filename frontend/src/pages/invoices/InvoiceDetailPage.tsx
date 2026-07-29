import { ArrowLeft, Calendar, FileText, Hash, Pencil, Plus, Wallet, X } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useInvoice, useUpdateInvoice } from "../../hooks/useInvoices";
import { useCreatePayment, useInvoicePayments } from "../../hooks/usePayments";
import { InvoiceForm } from "./InvoiceForm";
import { PaymentForm } from "./PaymentForm";
import { statusBadgeClass } from "./invoiceUtils";
import { formatDateTime } from "../tickets/ticketUtils";
import { formatBudget, formatDate } from "../objects/siteUtils";
import type { InvoiceUpdatePayload } from "../../types/invoice";
import type { PaymentCreatePayload } from "../../types/payment";

export default function InvoiceDetailPage() {
  const { id } = useParams();
  const invoiceId = Number(id);
  const [isEditing, setIsEditing] = useState(false);
  const [isPaymentOpen, setIsPaymentOpen] = useState(false);
  const { data: invoice, isPending, isError } = useInvoice(invoiceId);
  const updateInvoice = useUpdateInvoice();
  const { data: payments = [], isPending: isPaymentsPending } = useInvoicePayments(invoiceId);
  const createPayment = useCreatePayment();

  if (!Number.isInteger(invoiceId) || invoiceId < 1) return <DetailState>Invoice ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !invoice) return <DetailState>Invoiceni yuklashda xatolik yuz berdi.</DetailState>;

  const canAddPayment = invoice.payment_status !== "paid";

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/invoices" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Invoicelarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{invoice.invoice_number}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(invoice.payment_status)}`}>{invoice.payment_status_display}</span>
                <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{invoice.document_doc_number}</span>
              </div>
            </div>
            <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
              <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
            </button>
          </div>
          {updateInvoice.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
          {isEditing ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Invoiceni tahrirlash</h2>
              <InvoiceForm
                initialInvoice={invoice}
                submitLabel="Saqlash"
                isSubmitting={updateInvoice.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateInvoice.mutate({ invoiceId: invoice.id, payload: payload as InvoiceUpdatePayload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <InvoiceInformation invoice={invoice} />
          )}
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-gray-900">To'lovlar tarixi</h2>
            {canAddPayment && (
              <button type="button" onClick={() => setIsPaymentOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
                <Plus size={15} /> To'lov qo'shish
              </button>
            )}
          </div>

          {isPaymentsPending && <p className="text-sm text-gray-400">Yuklanmoqda...</p>}
          {!isPaymentsPending && payments.length === 0 && <p className="text-sm text-gray-400">To'lovlar yo'q</p>}
          {!isPaymentsPending && payments.length > 0 && (
            <div className="space-y-3">
              {payments.map((payment) => (
                <div key={payment.id} className="flex flex-wrap items-start justify-between gap-3 rounded-xl bg-gray-50 p-4">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 text-green-600"><Wallet size={17} /></span>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{formatBudget(payment.amount)}</p>
                      <p className="text-xs text-gray-500">{payment.payment_method || "—"}{payment.reference_number ? ` · ${payment.reference_number}` : ""}</p>
                      {payment.notes && <p className="mt-1 text-xs text-gray-500">{payment.notes}</p>}
                    </div>
                  </div>
                  <div className="text-right text-xs text-gray-400">
                    <p>{formatDateTime(payment.payment_date)}</p>
                    <p className="mt-0.5">{payment.performed_by_name}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {isPaymentOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-payment-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-payment-title" className="text-xl font-bold text-gray-900">Yangi to'lov</h2>
                <p className="mt-1 text-sm text-gray-500">Qoldiq: {formatBudget(invoice.remaining_amount)}</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsPaymentOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createPayment.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">To'lovni saqlab bo'lmadi. Summani tekshirib qayta urinib ko'ring.</p>}
            <PaymentForm
              isSubmitting={createPayment.isPending}
              onCancel={() => setIsPaymentOpen(false)}
              onSubmit={(payload: PaymentCreatePayload) => createPayment.mutate({ invoiceId: invoice.id, payload }, { onSuccess: () => setIsPaymentOpen(false) })}
            />
          </div>
        </div>
      )}
    </main>
  );
}

function InvoiceInformation({ invoice }: { invoice: NonNullable<ReturnType<typeof useInvoice>["data"]> }) {
  const details = [
    [<Hash size={17} />, "Shartnoma", invoice.contract_number || "—"],
    [<FileText size={17} />, "Hujjat", invoice.document_doc_number],
    [<Calendar size={17} />, "Sana", formatDate(invoice.invoice_date)],
    [<Calendar size={17} />, "To'lov muddati", invoice.due_date ? formatDate(invoice.due_date) : "—"],
    [<Wallet size={17} />, "Umumiy summa", formatBudget(invoice.total_amount)],
    [<Wallet size={17} />, "To'langan", formatBudget(invoice.paid_amount)],
    [<Wallet size={17} />, "Qoldiq", formatBudget(invoice.remaining_amount)],
  ] as const;

  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {details.map(([icon, label, value]) => (
        <div key={label} className="flex gap-3 rounded-xl bg-gray-50 p-4">
          <span className="mt-0.5 text-gray-400">{icon}</span>
          <div>
            <dt className="text-xs font-medium text-gray-500">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
          </div>
        </div>
      ))}
    </dl>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
