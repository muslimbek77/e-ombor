import { useState } from "react";
import { Plus, Search, X } from "lucide-react";

import { useContracts, useCreateContract } from "../../hooks/useContracts";
import { ContractCard } from "./ShartnomaContractCard";
import { ContractForm } from "./ShartnomaForm";
import type { ContractPayload } from "../../types/shartnoma";

// ── Main ───────────────────────────────────────────────────────────────────────

const ShartnomalarPage = () => {
  const [query, setQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: contracts = [], isLoading: loading, error } = useContracts();
  const createContract = useCreateContract();

  const filtered = contracts.filter((c) => {
    if (query.trim() === "") return true;
    const q = query.toLowerCase();
    return (
      c.supplier_name.toLowerCase().includes(q) ||
      c.contract_number.toLowerCase().includes(q) ||
      c.document_doc_number.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-full bg-gray-50 rounded-2xl p-6">
      <div className="space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-gray-900 text-2xl font-bold">Shartnomalar</h1>
            <p className="text-gray-400 text-sm mt-0.5">
              {loading ? "Yuklanmoqda..." : `${filtered.length} ta shartnoma`}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700"
            >
              <Plus size={16} /> Shartnoma qo'shish
            </button>
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Qidirish..."
                className="pl-9 pr-3 py-2 text-sm rounded-xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-56"
              />
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            Yuklanmoqda...
          </div>
        )}

        {!loading && error && (
          <div className="flex items-center justify-center h-40 text-red-500 text-sm">
            {error?.message}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            Shartnomalar topilmadi
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {filtered.map((contract) => (
              <ContractCard key={contract.id} contract={contract} />
            ))}
          </div>
        )}
      </div>

      {isCreateOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-contract-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 id="create-contract-title" className="text-xl font-bold text-gray-900">Yangi shartnoma</h2>
                <p className="mt-1 text-sm text-gray-500">Shartnoma ma'lumotlarini kiriting.</p>
              </div>
              <button type="button" aria-label="Yopish" onClick={() => setIsCreateOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createContract.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Shartnomani saqlab bo'lmadi. Ma'lumotlarni tekshirib, qayta urinib ko'ring.</p>}
            <ContractForm
              isSubmitting={createContract.isPending}
              onCancel={() => setIsCreateOpen(false)}
              onSubmit={(payload: ContractPayload) => createContract.mutate(payload, { onSuccess: () => setIsCreateOpen(false) })}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ShartnomalarPage;
