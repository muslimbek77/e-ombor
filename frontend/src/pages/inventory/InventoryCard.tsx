import { AlertTriangle, Building2, Layers, Tag } from "lucide-react";
import { Link } from "react-router-dom";
import type { InventoryItem } from "../../types/inventory";

export function InventoryCard({ item }: { item: InventoryItem }) {
  return (
    <Link
      to={`/inventory/${item.id}`}
      className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500"
    >
      <div
        className={`h-2 ${item.is_low_stock ? "bg-linear-to-r from-red-700 via-red-500 to-orange-400" : "bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]"}`}
      />
      <div className="p-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-base font-bold text-gray-900">{item.material_name}</h2>
            <p className="mt-1 flex items-center gap-1 text-xs font-medium text-gray-400">
              <Tag size={11} /> {item.material_code}
            </p>
          </div>
          {item.is_low_stock && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600">
              <AlertTriangle size={12} /> Kam qoldiq
            </span>
          )}
        </div>
        <div className="space-y-2.5 border-t border-gray-100 pt-3 text-sm text-gray-700">
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 shrink-0 text-gray-400"><Building2 size={14} /></span>
            <span>{item.warehouse_name} · {item.branch_name}</span>
          </div>
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 shrink-0 text-gray-400"><Layers size={14} /></span>
            <span className="font-semibold text-gray-900">{item.quantity}</span>
            <span className="text-gray-400">/ min {item.min_quantity}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
