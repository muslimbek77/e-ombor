import { useDeferredValue, useMemo, useState } from "react";
import { Plus, Search, X } from "lucide-react";
import { useCreateSite, useSites } from "../../hooks/useObjects";
import { SiteCard } from "./SiteCard";
import { SiteForm } from "./SiteForm";

const STATUS_FILTERS = [
  { value: "all", label: "Barchasi" },
  { value: "active", label: "Faol" },
  { value: "paused", label: "To'xtatilgan" },
  { value: "completed", label: "Tugallangan" },
] as const;

type StatusFilter = (typeof STATUS_FILTERS)[number]["value"];

export default function ObjectsPage() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const { data: sites = [], isPending, isError } = useSites();
  const createSite = useCreateSite();

  const filteredSites = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();

    return sites.filter((site) => {
      const matchesStatus =
        statusFilter === "all" || site.status === statusFilter;
      const matchesQuery =
        !normalizedQuery ||
        [site.name, site.code, site.branch_name].some((value) =>
          value.toLocaleLowerCase().includes(normalizedQuery),
        );

      return matchesStatus && matchesQuery;
    });
  }, [deferredQuery, sites, statusFilter]);

  return (
    <main className="min-h-full bg-gray-50 rounded-2xl p-6">
      <div className="w-full space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Obyektlar</h1>
            <p className="mt-0.5 text-sm text-gray-400">
              {isPending
                ? "Yuklanmoqda..."
                : `${filteredSites.length} ta obyekt`}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 cursor-pointer"
            >
              <Plus size={16} />
              Obyekt qo‘shish
            </button>
            <label className="relative">
              <span className="sr-only">Obyektlarni qidirish</span>
              <Search
                size={15}
                className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400"
              />
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Qidirish..."
                className="w-48 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30"
              />
            </label>

            <div className="flex items-center gap-1 rounded-xl border border-gray-200 bg-white p-1">
              {STATUS_FILTERS.map((filter) => (
                <button
                  key={filter.value}
                  type="button"
                  onClick={() => setStatusFilter(filter.value)}
                  className="cursor-pointer rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors"
                  style={
                    statusFilter === filter.value
                      ? { background: "#16a34a", color: "#fff" }
                      : { color: "#6b7280" }
                  }
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </header>

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && (
          <PageState className="text-red-500">
            Obyektlarni yuklashda xatolik yuz berdi
          </PageState>
        )}
        {!isPending && !isError && filteredSites.length === 0 && (
          <PageState>Obyektlar topilmadi</PageState>
        )}
        {!isPending && !isError && filteredSites.length > 0 && (
          <section
            className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
            aria-label="Obyektlar ro‘yxati"
          >
            {filteredSites.map((site) => (
              <SiteCard key={site.id} site={site} />
            ))}
          </section>
        )}
      </div>

      {isCreateOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-site-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
        >
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2
                  id="create-site-title"
                  className="text-xl font-bold text-gray-900"
                >
                  Yangi obyekt
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Obyekt ma’lumotlarini kiriting.
                </p>
              </div>
              <button
                type="button"
                aria-label="Yopish"
                onClick={() => setIsCreateOpen(false)}
                className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
              >
                <X size={18} />
              </button>
            </div>
            {createSite.isError && (
              <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                Obyektni yaratib bo‘lmadi. Ma’lumotlarni tekshirib, qayta urinib
                ko‘ring.
              </p>
            )}
            <SiteForm
              submitLabel="Yaratish"
              isSubmitting={createSite.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload) =>
                createSite.mutate(payload, {
                  onSuccess: () => setIsCreateOpen(false),
                })
              }
            />
          </div>
        </div>
      )}
    </main>
  );
}

function PageState({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`flex h-40 items-center justify-center text-sm text-gray-400 ${className}`}
    >
      {children}
    </div>
  );
}
