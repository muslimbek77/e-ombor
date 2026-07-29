import { AlertTriangle, Bell, Building2, FileText, Package, Ticket, Warehouse } from "lucide-react";
import { useDashboard } from "../hooks/useDashboard";

const currencyFormatter = new Intl.NumberFormat("uz-UZ", { maximumFractionDigits: 0 });

function formatSum(value: string) {
  return `${currencyFormatter.format(Number(value))} so'm`;
}

const DOCUMENT_STATUS_STYLES: Record<string, string> = {
  created: "bg-gray-100 text-gray-600",
  architecture: "bg-blue-50 text-blue-700",
  ceo: "bg-indigo-50 text-indigo-700",
  approved: "bg-teal-50 text-teal-700",
  contract: "bg-purple-50 text-purple-700",
  payment: "bg-amber-50 text-amber-700",
  delivering: "bg-cyan-50 text-cyan-700",
  received: "bg-lime-50 text-lime-700",
  closed: "bg-green-50 text-green-700",
  rejected: "bg-red-50 text-red-700",
};

function documentStatusBadgeClass(status: string) {
  return DOCUMENT_STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600";
}

const TICKET_STATUS_STYLES: Record<string, string> = {
  open: "bg-red-50 text-red-700",
  in_progress: "bg-amber-50 text-amber-700",
  resolved: "bg-lime-50 text-lime-700",
  closed: "bg-green-50 text-green-700",
};

function ticketStatusBadgeClass(status: string) {
  return TICKET_STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600";
}

const TICKET_PRIORITY_STYLES: Record<string, string> = {
  low: "text-gray-400",
  medium: "text-blue-500",
  high: "text-amber-600",
  urgent: "text-red-600 font-semibold",
};

function ticketPriorityClass(priority: string) {
  return TICKET_PRIORITY_STYLES[priority] ?? "text-gray-400";
}

function StatCard({ icon, label, value, accent }: { icon: React.ReactNode; label: string; value: number; accent: string }) {
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

export default function Dashboard() {
  const { data, isPending, isError } = useDashboard();

  if (isPending) return <PanelState>Yuklanmoqda...</PanelState>;
  if (isError || !data) return <PanelState>Boshqaruv panelini yuklashda xatolik yuz berdi</PanelState>;

  return (
    <div className="space-y-6">
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard icon={<FileText size={18} className="text-blue-600" />} label="Hujjatlar" value={data.total_documents} accent="bg-blue-50" />
        <StatCard icon={<AlertTriangle size={18} className="text-amber-600" />} label="Tasdiq kutilmoqda" value={data.pending_approvals} accent="bg-amber-50" />
        <StatCard icon={<Package size={18} className="text-purple-600" />} label="Materiallar" value={data.total_materials} accent="bg-purple-50" />
        <StatCard icon={<Warehouse size={18} className="text-green-600" />} label="Omborlar" value={data.total_warehouses} accent="bg-green-50" />
        <StatCard icon={<Building2 size={18} className="text-teal-600" />} label="Obyektlar" value={data.total_sites} accent="bg-teal-50" />
        <StatCard icon={<AlertTriangle size={18} className="text-red-600" />} label="Kam qolgan" value={data.low_stock_items} accent="bg-red-50" />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><FileText size={16} /> So'nggi hujjatlar</h2>
          {data.recent_documents.length === 0 && <PanelState>Hujjatlar topilmadi</PanelState>}
          <ul className="divide-y divide-gray-100">
            {data.recent_documents.map((doc) => (
              <li key={doc.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                <div className="min-w-0"><p className="truncate font-medium text-gray-800">{doc.title}</p><p className="text-xs text-gray-400">{doc.doc_number}</p></div>
                <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${documentStatusBadgeClass(doc.status)}`}>{doc.status_display}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><Ticket size={16} /> So'nggi murojaatlar</h2>
          {data.recent_tickets.length === 0 && <PanelState>Murojaatlar topilmadi</PanelState>}
          <ul className="divide-y divide-gray-100">
            {data.recent_tickets.map((ticket) => (
              <li key={ticket.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                <div className="min-w-0"><p className="truncate font-medium text-gray-800">{ticket.title}</p><p className={`text-xs ${ticketPriorityClass(ticket.priority)}`}>{ticket.priority_display}</p></div>
                <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${ticketStatusBadgeClass(ticket.status)}`}>{ticket.status_display}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900"><Bell size={16} /> Bildirishnomalar</h2>
          {data.notifications.length === 0 && <PanelState>Bildirishnomalar yo'q</PanelState>}
          <ul className="divide-y divide-gray-100">
            {data.notifications.map((notification) => (
              <li key={notification.id} className="flex items-start gap-2 py-2.5 text-sm">
                {!notification.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-green-500" />}
                <div className="min-w-0"><p className="truncate font-medium text-gray-800">{notification.title}</p><p className="truncate text-xs text-gray-400">{notification.message}</p></div>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-gray-900">Moliya xulosasi</h2>
          <dl className="space-y-2.5 text-sm">
            <div className="flex items-center justify-between"><dt className="text-gray-400">Umumiy hisob-fakturalar</dt><dd className="font-semibold text-gray-800">{formatSum(data.payment_summary.total_invoiced)}</dd></div>
            <div className="flex items-center justify-between"><dt className="text-gray-400">To'langan</dt><dd className="font-semibold text-green-600">{formatSum(data.payment_summary.total_paid)}</dd></div>
            <div className="flex items-center justify-between"><dt className="text-gray-400">Qoldiq</dt><dd className="font-semibold text-red-600">{formatSum(data.payment_summary.remaining)}</dd></div>
            <div className="flex items-center justify-between border-t border-gray-100 pt-2.5"><dt className="text-gray-400">Obyektlar byudjeti</dt><dd className="font-semibold text-gray-800">{formatSum(data.site_budget_summary.total_budget)}</dd></div>
          </dl>
        </div>
      </section>
    </div>
  );
}
