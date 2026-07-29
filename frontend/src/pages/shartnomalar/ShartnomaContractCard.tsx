import { useNavigate } from "react-router-dom";
import type { Contract } from "../../types/shartnoma";
import { Calendar, ChevronRight, FileText, Hash, Wallet } from "lucide-react";
import { isExpired, isExpiringSoon } from "./ShartnomaUtilis";
import { formatBudget, formatDate } from "../objects/siteUtils";

export function ContractCard({ contract }: { contract: Contract }) {
  const navigate = useNavigate();
  const expired = isExpired(contract.end_date);
  const expiring = !expired && isExpiringSoon(contract.end_date);

  const badge = expired
    ? { bg: "#fee2e2", color: "#b91c1c", label: "Muddati tugagan" }
    : expiring
      ? { bg: "#fef9c3", color: "#854d0e", label: "Muddati yaqinlashmoqda" }
      : { bg: "#dcfce7", color: "#15803d", label: "Amal qilmoqda" };

  return (
    <div
      onClick={() => navigate(`/contracts/${contract.id}`)}
      className="bg-white rounded-2xl overflow-hidden hover:-translate-y-0.5 transition-transform cursor-pointer"
      style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
    >
      <div
        className="h-2"
        style={{
          background:
            "linear-gradient(90deg, #0f1c14 0%, #16a34a 60%, #22c55e 100%)",
        }}
      />

      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            <h3 className="text-gray-900 text-base font-bold leading-tight truncate">
              {contract.supplier_name}
            </h3>
            <div className="flex items-center gap-1 mt-1 text-xs text-gray-400 font-medium">
              <Hash size={11} />
              {contract.contract_number}
            </div>
          </div>
          <span
            className="inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full flex-shrink-0"
            style={{ background: badge.bg, color: badge.color }}
          >
            {badge.label}
          </span>
        </div>

        <p className="text-sm text-gray-500 mb-3 line-clamp-2">
          {contract.description}
        </p>

        <div className="space-y-2.5 pt-2 border-t border-gray-100">
          <div className="flex items-center gap-2.5 text-sm">
            <FileText size={14} className="text-gray-400 flex-shrink-0" />
            <span className="text-gray-700">
              {contract.document_doc_number}
            </span>
          </div>
          <div className="flex items-center gap-2.5 text-sm">
            <Calendar size={14} className="text-gray-400 flex-shrink-0" />
            <span className="text-gray-700">
              {formatDate(contract.start_date)} —{" "}
              {formatDate(contract.end_date)}
            </span>
          </div>
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2.5 text-sm">
              <Wallet size={14} className="text-gray-400 flex-shrink-0" />
              <span className="text-gray-800 font-semibold">
                {formatBudget(contract.total_amount)}
              </span>
            </div>
            <ChevronRight size={16} className="text-gray-300" />
          </div>
        </div>
      </div>
    </div>
  );
}
