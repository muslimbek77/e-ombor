import { Calendar, Hash, MapPin, User } from "lucide-react";
import { Link } from "react-router-dom";
import type { ProductionRequest } from "../../types/productionRequest";
import { formatDateTime, statusBadgeClass } from "./productionRequestUtils";

export function ProductionRequestCard({ request }: { request: ProductionRequest }) {
  return (
    <Link to={`/production-requests/${request.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="min-w-0 truncate text-base font-bold text-gray-900">{request.title}</h2>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(request.status)}`}>{request.status_display}</span>
        </div>
        <p className="mb-3 line-clamp-2 text-sm text-gray-500">{request.description || "Tavsif kiritilmagan"}</p>
        <div className="space-y-2 border-t border-gray-100 pt-3 text-sm text-gray-700">
          <Info icon={<Hash size={14} />} value={request.request_number} />
          <Info icon={<MapPin size={14} />} value={request.site_name || "—"} />
          <Info icon={<User size={14} />} value={request.created_by_name || "Noma'lum"} />
          <Info icon={<Calendar size={14} />} value={formatDateTime(request.created_at)} />
        </div>
      </div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
