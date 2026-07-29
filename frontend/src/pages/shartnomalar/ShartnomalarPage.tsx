import { useState } from "react";
import { Search } from "lucide-react";

import { useContracts } from "../../hooks/useContracts";
import { ContractCard } from "./ShartnomaContractCard";

// ── Main ───────────────────────────────────────────────────────────────────────

const ShartnomalarPage = () => {
  const [query, setQuery] = useState("");

  const { data: contracts = [], isLoading: loading, error } = useContracts();

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
    </div>
  );
};

export default ShartnomalarPage;
