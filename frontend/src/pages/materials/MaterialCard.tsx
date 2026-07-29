import { Calendar, Layers, Ruler, Tag } from "lucide-react";
import { Link } from "react-router-dom";
import type { Material } from "../../types/material";
import { formatDate } from "../objects/siteUtils";

export function MaterialCard({ material }: { material: Material }) {
  return <Link to={`/materials/${material.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500"><div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" /><div className="p-5"><div className="mb-4 flex items-start justify-between gap-3"><div className="min-w-0"><h2 className="truncate text-base font-bold text-gray-900">{material.name}</h2><p className="mt-1 flex items-center gap-1 text-xs font-medium text-gray-400"><Tag size={11} /> {material.code}</p></div><span className="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600"><Layers className="mr-1 inline" size={12} />{material.category}</span></div><div className="space-y-2.5 border-t border-gray-100 pt-3 text-sm text-gray-700"><Info icon={<Ruler size={14} />} value={material.unit} /><Info icon={<Calendar size={14} />} value={formatDate(material.created_at)} /></div></div></Link>;
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
