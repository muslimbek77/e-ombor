import { Plus, Search, X } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useCreateProductionRequest, useProductionRequests } from "../../hooks/useProductionRequests";
import { ProductionRequestCard } from "./ProductionRequestCard";
import { ProductionRequestForm } from "./ProductionRequestForm";
import { STATUS_OPTIONS } from "./productionRequestUtils";
import type { ProductionRequestCreatePayload } from "../../types/productionRequest";

const STATUS_FILTERS = [{ value: "all", label: "Barchasi" }, ...STATUS_OPTIONS] as const;

type StatusFilter = (typeof STATUS_FILTERS)[number]["value"];

export default function ProductionRequestsPage() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const { data: requests = [], isPending, isError } = useProductionRequests();
  const createRequest = useCreateProductionRequest();

  const filteredRequests = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    return requests.filter((request) => {
      const matchesStatus = statusFilter === "all" || request.status === statusFilter;
      const matchesQuery = !normalizedQuery || [request.title, request.description, request.request_number, request.site_name].some((value) => (value ?? "").toLocaleLowerCase().includes(normalizedQuery));
      return matchesStatus && matchesQuery;
    });
  }, [deferredQuery, statusFilter, requests]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ishlab chiqarish zayavkalari</h1>
            <p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredRequests.length} ta zayavka`}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setIsCreateOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
              <Plus size={16} /> Zayavka qo'shish
            </button>
            <label className="relative">
              <span className="sr-only">Zayavkalarni qidirish</span>
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
          </div>
        </header>

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Zayavkalarni yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredRequests.length === 0 && <PageState>Zayavkalar topilmadi</PageState>}
        {!isPending && !isError && filteredRequests.length > 0 && (
          <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Zayavkalar ro'yxati">
            {filteredRequests.map((request) => <ProductionRequestCard key={request.id} request={request} />)}
          </section>
        )}
      </div>

      {isCreateOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-request-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-request-title" className="text-xl font-bold text-gray-900">Yangi zayavka</h2>
                <p className="mt-1 text-sm text-gray-500">Zayavka raqami avtomatik beriladi.</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createRequest.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Zayavkani yaratib bo'lmadi. Ma'lumotlarni tekshirib, qayta urinib ko'ring.</p>}
            <ProductionRequestForm
              isSubmitting={createRequest.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload) => createRequest.mutate(payload as ProductionRequestCreatePayload, { onSuccess: () => setIsCreateOpen(false) })}
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
