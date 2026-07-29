import { Calendar, Package, User, Wallet } from "lucide-react";
import { Link } from "react-router-dom";
import type { PurchaseOrder } from "../../types/purchaseOrder";
import { formatBudget, formatDate } from "../objects/siteUtils";

export function PurchaseOrderCard({ purchaseOrder }: { purchaseOrder: PurchaseOrder }) {
  return <Link to={`/purchases/${purchaseOrder.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500"><div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" /><div className="p-5"><div className="mb-4 flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-base font-bold text-gray-900">{purchaseOrder.title}</h2><p className="mt-1 text-xs font-medium text-gray-400">{purchaseOrder.doc_number}</p></div><span className="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600">{purchaseOrder.doc_status}</span></div><div className="space-y-2.5 border-t border-gray-100 pt-3 text-sm text-gray-700"><Info icon={<User size={14} />} value={purchaseOrder.supplier_name || "—"} /><Info icon={<Wallet size={14} />} value={formatBudget(purchaseOrder.total_amount)} /><Info icon={<Package size={14} />} value={`${purchaseOrder.items.length} ta mahsulot`} /><Info icon={<Calendar size={14} />} value={formatDate(purchaseOrder.created_at)} /></div></div></Link>;
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
