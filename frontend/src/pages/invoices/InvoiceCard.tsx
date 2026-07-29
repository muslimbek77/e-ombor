import { Calendar, FileText, Hash, Wallet } from "lucide-react";
import { Link } from "react-router-dom";
import type { Invoice } from "../../types/invoice";
import { formatBudget, formatDate } from "../objects/siteUtils";
import { isOverdue, statusBadgeClass } from "./invoiceUtils";

export function InvoiceCard({ invoice }: { invoice: Invoice }) {
  const overdue = isOverdue(invoice);

  return (
    <Link to={`/invoices/${invoice.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="min-w-0 truncate text-base font-bold text-gray-900">{invoice.invoice_number}</h2>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(invoice.payment_status)}`}>{invoice.payment_status_display}</span>
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{invoice.document_doc_number}</span>
          {overdue && <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700">Muddati o'tgan</span>}
        </div>
        <div className="space-y-2 border-t border-gray-100 pt-3 text-sm text-gray-700">
          {invoice.contract_number && <Info icon={<Hash size={14} />} value={invoice.contract_number} />}
          <Info icon={<Calendar size={14} />} value={formatDate(invoice.invoice_date)} />
          {invoice.due_date && <Info icon={<FileText size={14} />} value={`Muddat: ${formatDate(invoice.due_date)}`} />}
          <div className="flex items-center justify-between pt-1">
            <Info icon={<Wallet size={14} />} value={`${formatBudget(invoice.paid_amount)} / ${formatBudget(invoice.total_amount)}`} />
          </div>
        </div>
      </div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
