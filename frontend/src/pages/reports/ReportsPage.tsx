import { AlertTriangle, BarChart2, FileText, History, Package, Ticket, Wallet } from "lucide-react";
import { useAnalyticsOverview } from "../../hooks/useAnalytics";
import { formatBudget, formatDate } from "../objects/siteUtils";
import { actionBadgeClass, actionLabel, formatDateTime } from "../audit-logs/auditLogUtils";
import { statusBadgeClass as invoiceStatusBadgeClass } from "../invoices/invoiceUtils";
import { CategoryBarChart } from "./CategoryBarChart";
import { DOCUMENT_STATUS_ORDER, DOCUMENT_TYPE_ORDER, TICKET_PRIORITY_ORDER, TICKET_STATUS_ORDER, formatCappedCount } from "./reportsUtils";

function StatTile({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: string | number; accent: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${accent}`}>{icon}</div>
      <div>
        <p className="text-xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
      </div>
    </div>
  );
}

function PanelState({ children }: { children: React.ReactNode }) {
  return <p className="py-6 text-center text-sm text-gray-400">{children}</p>;
}

export default function ReportsPage() {
  const { data, isPending, isError } = useAnalyticsOverview();

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header>
          <h1 className="text-2xl font-bold text-gray-900">Hisobotlar</h1>
          <p className="mt-0.5 text-sm text-gray-400">Hujjatlar, murojaatlar va zaxiralar bo'yicha umumiy ko'rsatkichlar</p>
        </header>

        {isPending && <PanelState>Yuklanmoqda...</PanelState>}
        {isError && <PanelState>Hisobotlarni yuklashda xatolik yuz berdi</PanelState>}

        {data && (
          <>
            <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StatTile icon={<FileText size={18} className="text-blue-600" />} label="Jami hujjatlar" accent="bg-blue-50" value={data.documents_by_type.reduce((sum, item) => sum + item.total, 0)} />
              <StatTile icon={<Ticket size={18} className="text-purple-600" />} label="Jami murojaatlar" accent="bg-purple-50" value={data.tickets_by_status.reduce((sum, item) => sum + item.total, 0)} />
              <StatTile icon={<Wallet size={18} className="text-red-600" />} label="Muddati o'tgan hisob-fakturalar" accent="bg-red-50" value={formatCappedCount(data.overdue_invoices.length, 10)} />
              <StatTile icon={<Package size={18} className="text-amber-600" />} label="Kam zaxira mahsulotlar" accent="bg-amber-50" value={formatCappedCount(data.low_stock_items.length, 10)} />
            </section>

            <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <CategoryBarChart title="Hujjatlar turi bo'yicha" icon={<FileText size={16} />} order={DOCUMENT_TYPE_ORDER} counts={data.documents_by_type.map((item) => ({ value: item.doc_type, total: item.total }))} />
              <CategoryBarChart title="Hujjatlar holati bo'yicha" icon={<BarChart2 size={16} />} order={DOCUMENT_STATUS_ORDER} counts={data.documents_by_status.map((item) => ({ value: item.status, total: item.total }))} />
              <CategoryBarChart title="Murojaatlar ustuvorligi bo'yicha" icon={<AlertTriangle size={16} />} order={TICKET_PRIORITY_ORDER} counts={data.tickets_by_priority.map((item) => ({ value: item.priority, total: item.total }))} />
              <CategoryBarChart title="Murojaatlar holati bo'yicha" icon={<Ticket size={16} />} order={TICKET_STATUS_ORDER} counts={data.tickets_by_status.map((item) => ({ value: item.status, total: item.total }))} />
            </section>

            <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><Wallet size={16} /> Muddati o'tgan hisob-fakturalar</h2>
                {data.overdue_invoices.length === 0 && <PanelState>Muddati o'tgan hisob-fakturalar yo'q</PanelState>}
                {data.overdue_invoices.length > 0 && (
                  <ul className="divide-y divide-gray-100">
                    {data.overdue_invoices.map((invoice) => (
                      <li key={invoice.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                        <div className="min-w-0">
                          <p className="truncate font-medium text-gray-800">{invoice.invoice_number}</p>
                          <p className="text-xs text-gray-400">Muddat: {formatDate(invoice.due_date)} · Qoldiq: {formatBudget(invoice.remaining_amount)}</p>
                        </div>
                        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${invoiceStatusBadgeClass(invoice.payment_status)}`}>{invoice.payment_status_display}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><Package size={16} /> Kam zaxira mahsulotlar</h2>
                {data.low_stock_items.length === 0 && <PanelState>Kam zaxira mahsulotlar yo'q</PanelState>}
                {data.low_stock_items.length > 0 && (
                  <ul className="divide-y divide-gray-100">
                    {data.low_stock_items.map((item) => (
                      <li key={item.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                        <div className="min-w-0">
                          <p className="truncate font-medium text-gray-800">{item.material_name}</p>
                          <p className="text-xs text-gray-400">{item.warehouse_name}</p>
                        </div>
                        <span className="shrink-0 text-xs font-semibold text-amber-700">{item.quantity} / {item.min_quantity}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
              <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><History size={16} /> So'nggi audit yozuvlari</h2>
              {data.recent_audit_logs.length === 0 && <PanelState>Audit yozuvlari topilmadi</PanelState>}
              {data.recent_audit_logs.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 text-xs font-semibold tracking-wide text-gray-400 uppercase">
                        <th className="px-2 py-2">Vaqt</th>
                        <th className="px-2 py-2">Foydalanuvchi</th>
                        <th className="px-2 py-2">Amal</th>
                        <th className="px-2 py-2">Model</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_audit_logs.map((log) => (
                        <tr key={log.id} className="border-b border-gray-50 last:border-0">
                          <td className="px-2 py-2 whitespace-nowrap text-gray-500">{formatDateTime(log.created_at)}</td>
                          <td className="px-2 py-2 font-medium text-gray-800">{log.user_name ?? "—"}</td>
                          <td className="px-2 py-2"><span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${actionBadgeClass(log.action)}`}>{actionLabel(log.action)}</span></td>
                          <td className="px-2 py-2 text-gray-600">{log.model_name}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
