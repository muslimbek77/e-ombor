import { Plus, Search, X } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useCreateSupplier, useSuppliers } from "../../hooks/useSuppliers";
import { SupplierCard } from "./SupplierCard";
import { SupplierForm } from "./SupplierForm";

export default function SuppliersPage() {
  const [query, setQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const { data: suppliers = [], isPending, isError } = useSuppliers();
  const createSupplier = useCreateSupplier();

  const filteredSuppliers = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    if (!normalizedQuery) return suppliers;
    return suppliers.filter((supplier) => [supplier.name, supplier.code, supplier.contact_person, supplier.phone, supplier.email].some((value) => value.toLocaleLowerCase().includes(normalizedQuery)));
  }, [deferredQuery, suppliers]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold text-gray-900">Supplierlar</h1><p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredSuppliers.length} ta supplier`}</p></div><div className="flex flex-wrap items-center gap-2"><button type="button" onClick={() => setIsCreateOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700"><Plus size={16} /> Supplier qo‘shish</button><label className="relative"><span className="sr-only">Supplierlarni qidirish</span><Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400" /><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Qidirish..." className="w-52 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30" /></label></div></header>
        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Supplierlarni yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredSuppliers.length === 0 && <PageState>Supplierlar topilmadi</PageState>}
        {!isPending && !isError && filteredSuppliers.length > 0 && <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Supplierlar ro‘yxati">{filteredSuppliers.map((supplier) => <SupplierCard key={supplier.id} supplier={supplier} />)}</section>}
      </div>
      {isCreateOpen && <div role="dialog" aria-modal="true" aria-labelledby="create-supplier-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"><div className="mb-5 flex items-center justify-between gap-4"><div><h2 id="create-supplier-title" className="text-xl font-bold text-gray-900">Yangi supplier</h2><p className="mt-1 text-sm text-gray-500">Supplier ma’lumotlarini kiriting.</p></div><button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button></div>{createSupplier.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Supplierni yaratib bo‘lmadi. Ma’lumotlarni tekshirib, qayta urinib ko‘ring.</p>}<SupplierForm isSubmitting={createSupplier.isPending} onCancel={() => setIsCreateOpen(false)} onSubmit={(payload) => createSupplier.mutate(payload, { onSuccess: () => setIsCreateOpen(false) })} /></div></div>}
    </main>
  );
}

function PageState({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`flex h-40 items-center justify-center text-sm text-gray-400 ${className}`}>{children}</div>;
}
