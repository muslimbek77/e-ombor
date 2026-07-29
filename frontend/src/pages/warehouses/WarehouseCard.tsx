import { BellRing, Building2, Calendar, MapPin, Tag } from "lucide-react";
import { Link } from "react-router-dom";
import type { Warehouse } from "../../types/warehouse";
import { formatDate } from "../objects/siteUtils";

export function WarehouseCard({ warehouse }: { warehouse: Warehouse }) {
  return <Link to={`/warehouse/${warehouse.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500"><div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" /><div className="p-5"><div className="mb-4 flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-base font-bold text-gray-900">{warehouse.name}</h2><p className="mt-1 flex items-center gap-1 text-xs font-medium text-gray-400"><Tag size={11} /> {warehouse.code}</p></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${warehouse.min_stock_alert ? "bg-amber-100 text-amber-800" : "bg-gray-100 text-gray-600"}`}><BellRing className="mr-1 inline" size={12} />{warehouse.min_stock_alert ? "Ogohlantirish faol" : "Ogohlantirish o‘chiq"}</span></div><div className="space-y-2.5 border-t border-gray-100 pt-3 text-sm text-gray-700"><Info icon={<Building2 size={14} />} value={warehouse.branch_name} /><Info icon={<MapPin size={14} />} value={warehouse.address} /><Info icon={<Calendar size={14} />} value={formatDate(warehouse.created_at)} /></div></div></Link>;
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
