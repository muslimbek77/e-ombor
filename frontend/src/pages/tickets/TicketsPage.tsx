import { Download, Plus, Search, X } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useCreateTicket, useExportTickets, useTickets } from "../../hooks/useTickets";
import { TicketCard } from "./TicketCard";
import { TicketForm } from "./TicketForm";
import { useIsControlRole } from "../../lib/permissions";
import type { TicketCreatePayload } from "../../types/ticket";

const STATUS_FILTERS = [
  { value: "all", label: "Barchasi" },
  { value: "open", label: "Ochiq" },
  { value: "in_progress", label: "Jarayonda" },
  { value: "resolved", label: "Yechildi" },
  { value: "closed", label: "Yopildi" },
] as const;

type StatusFilter = (typeof STATUS_FILTERS)[number]["value"];

export default function TicketsPage() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const { data: tickets = [], isPending, isError } = useTickets();
  const createTicket = useCreateTicket();
  const exportTickets = useExportTickets();
  // Nazorat roli murojaat ham yarata olmaydi (server: 403).
  const isReadOnly = useIsControlRole();

  const filteredTickets = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    return tickets.filter((ticket) => {
      const matchesStatus = statusFilter === "all" || ticket.status === statusFilter;
      const matchesQuery = !normalizedQuery || [ticket.title, ticket.description, ticket.site_name, ticket.branch_name].some((value) => value.toLocaleLowerCase().includes(normalizedQuery));
      return matchesStatus && matchesQuery;
    });
  }, [deferredQuery, statusFilter, tickets]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Murojaatlar</h1>
            <p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredTickets.length} ta murojaat`}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {!isReadOnly && (
              <button type="button" onClick={() => setIsCreateOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
                <Plus size={16} /> Murojaat qo'shish
              </button>
            )}
            <label className="relative">
              <span className="sr-only">Murojaatlarni qidirish</span>
              <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400" />
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Qidirish..." className="w-48 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30" />
            </label>
            <div className="flex items-center gap-1 rounded-xl border border-gray-200 bg-white p-1">
              {STATUS_FILTERS.map((filter) => (
                <button key={filter.value} type="button" onClick={() => setStatusFilter(filter.value)} className="cursor-pointer rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors" style={statusFilter === filter.value ? { background: "#16a34a", color: "#fff" } : { color: "#6b7280" }}>
                  {filter.label}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={() => exportTickets.mutate(statusFilter === "all" ? undefined : { status: statusFilter })}
              disabled={exportTickets.isPending}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Download size={15} /> {exportTickets.isPending ? "Yuklab olinmoqda..." : "Eksport"}
            </button>
          </div>
        </header>

        {exportTickets.isError && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">Murojaatlarni eksport qilib bo'lmadi.</p>}

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Murojaatlarni yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredTickets.length === 0 && <PageState>Murojaatlar topilmadi</PageState>}
        {!isPending && !isError && filteredTickets.length > 0 && (
          <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Murojaatlar ro'yxati">
            {filteredTickets.map((ticket) => <TicketCard key={ticket.id} ticket={ticket} />)}
          </section>
        )}
      </div>

      {isCreateOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-ticket-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-ticket-title" className="text-xl font-bold text-gray-900">Yangi murojaat</h2>
                <p className="mt-1 text-sm text-gray-500">Murojaat ma'lumotlarini kiriting.</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createTicket.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Murojaatni yaratib bo'lmadi. Ma'lumotlarni tekshirib, qayta urinib ko'ring.</p>}
            <TicketForm
              isSubmitting={createTicket.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload) => createTicket.mutate(payload as TicketCreatePayload, { onSuccess: () => setIsCreateOpen(false) })}
            />
          </div>
        </div>
      )}
    </main>
  );
}

function PageState({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`flex h-40 items-center justify-center text-sm text-gray-400 ${className}`}>{children}</div>;
}
