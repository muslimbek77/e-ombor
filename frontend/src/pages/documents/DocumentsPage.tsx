import { Archive, Plus, Search, X } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useCreateDocument, useDocuments } from "../../hooks/useDocuments";
import { DocumentCard } from "./DocumentCard";
import { DocumentForm } from "./DocumentForm";
import { STATUS_FILTERS } from "./documentUtils";
import type { DocumentCreatePayload } from "../../types/document";

type StatusFilter = (typeof STATUS_FILTERS)[number]["value"];

export default function DocumentsPage() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showArchived, setShowArchived] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const { data: documents = [], isPending, isError } = useDocuments({ archived: showArchived ? "true" : "false" });
  const createDocument = useCreateDocument();

  const filteredDocuments = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    return documents.filter((document) => {
      const matchesStatus = statusFilter === "all" || document.status === statusFilter;
      const matchesQuery = !normalizedQuery || [document.title, document.doc_number, document.description].some((value) => value.toLocaleLowerCase().includes(normalizedQuery));
      return matchesStatus && matchesQuery;
    });
  }, [deferredQuery, statusFilter, documents]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Hujjatlar</h1>
            <p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredDocuments.length} ta hujjat`}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setIsCreateOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
              <Plus size={16} /> Hujjat qo'shish
            </button>
            <button
              type="button"
              onClick={() => setShowArchived((value) => !value)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              style={showArchived ? { background: "#f3f4f6" } : undefined}
            >
              <Archive size={15} /> {showArchived ? "Arxivlanganlar" : "Faol hujjatlar"}
            </button>
            <label className="relative">
              <span className="sr-only">Hujjatlarni qidirish</span>
              <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400" />
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Qidirish..." className="w-48 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30" />
            </label>
          </div>
        </header>

        <div className="flex flex-wrap items-center gap-1 rounded-xl border border-gray-200 bg-white p-1">
          {STATUS_FILTERS.map((filter) => (
            <button key={filter.value} type="button" onClick={() => setStatusFilter(filter.value)} className="cursor-pointer rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors" style={statusFilter === filter.value ? { background: "#16a34a", color: "#fff" } : { color: "#6b7280" }}>
              {filter.label}
            </button>
          ))}
        </div>

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Hujjatlarni yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredDocuments.length === 0 && <PageState>Hujjatlar topilmadi</PageState>}
        {!isPending && !isError && filteredDocuments.length > 0 && (
          <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Hujjatlar ro'yxati">
            {filteredDocuments.map((document) => <DocumentCard key={document.id} document={document} />)}
          </section>
        )}
      </div>

      {isCreateOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-document-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-document-title" className="text-xl font-bold text-gray-900">Yangi hujjat</h2>
                <p className="mt-1 text-sm text-gray-500">Hujjat ma'lumotlarini kiriting.</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createDocument.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Hujjat yaratib bo'lmadi. Ma'lumotlarni tekshirib, qayta urinib ko'ring.</p>}
            <DocumentForm
              isSubmitting={createDocument.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload) => createDocument.mutate(payload as DocumentCreatePayload, { onSuccess: () => setIsCreateOpen(false) })}
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
