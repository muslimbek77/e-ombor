import { AlertTriangle, Plus, Search, X } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useCreateInventoryItem, useInventory } from "../../hooks/useInventory";
import { useWarehouses } from "../../hooks/useWarehouses";
import { InventoryCard } from "./InventoryCard";
import { InventoryForm } from "./InventoryForm";
import type { InventoryItemPayload } from "../../types/inventory";

export default function InventoryPage() {
  const [query, setQuery] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);

  const { data: warehouses = [] } = useWarehouses();
  const { data: items = [], isPending, isError } = useInventory(warehouseFilter ? { warehouse: Number(warehouseFilter) } : undefined);
  const createInventoryItem = useCreateInventoryItem();

  const filteredItems = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    return items.filter((item) => {
      const matchesLowStock = !lowStockOnly || item.is_low_stock;
      const matchesQuery = !normalizedQuery || [item.material_name, item.material_code, item.warehouse_name].some((value) => value.toLocaleLowerCase().includes(normalizedQuery));
      return matchesLowStock && matchesQuery;
    });
  }, [deferredQuery, lowStockOnly, items]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Inventar</h1>
            <p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredItems.length} ta zaxira yozuvi`}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setIsCreateOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
              <Plus size={16} /> Zaxira qo'shish
            </button>
            <label className="relative">
              <span className="sr-only">Inventarni qidirish</span>
              <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400" />
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Qidirish..." className="w-48 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30" />
            </label>
            <select value={warehouseFilter} onChange={(event) => setWarehouseFilter(event.target.value)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30">
              <option value="">Barcha omborlar</option>
              {warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name}</option>)}
            </select>
            <button
              type="button"
              onClick={() => setLowStockOnly((value) => !value)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-semibold transition-colors"
              style={lowStockOnly ? { background: "#fef2f2", borderColor: "#fecaca", color: "#dc2626" } : { borderColor: "#e5e7eb", color: "#6b7280" }}
            >
              <AlertTriangle size={14} /> Kam qoldiqlar
            </button>
          </div>
        </header>

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Inventarni yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredItems.length === 0 && <PageState>Zaxira yozuvlari topilmadi</PageState>}
        {!isPending && !isError && filteredItems.length > 0 && (
          <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Inventar ro'yxati">
            {filteredItems.map((item) => <InventoryCard key={item.id} item={item} />)}
          </section>
        )}
      </div>

      {isCreateOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-inventory-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-inventory-title" className="text-xl font-bold text-gray-900">Yangi zaxira</h2>
                <p className="mt-1 text-sm text-gray-500">Omborga material va boshlang'ich miqdorni biriktiring.</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createInventoryItem.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Zaxirani saqlab bo'lmadi. Bu ombor uchun bu material allaqachon mavjud bo'lishi mumkin.</p>}
            <InventoryForm
              isSubmitting={createInventoryItem.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload: InventoryItemPayload) => createInventoryItem.mutate(payload, { onSuccess: () => setIsCreateOpen(false) })}
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
