import { Building2, Calendar, MapPin, User } from "lucide-react";
import { Link } from "react-router-dom";
import type { Ticket } from "../../types/ticket";
import { formatDateTime, priorityBadgeClass, statusBadgeClass } from "./ticketUtils";

export function TicketCard({ ticket }: { ticket: Ticket }) {
  return (
    <Link to={`/tickets/${ticket.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="min-w-0 truncate text-base font-bold text-gray-900">{ticket.title}</h2>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(ticket.status)}`}>{ticket.status_display}</span>
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${priorityBadgeClass(ticket.priority)}`}>{ticket.priority_display}</span>
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{ticket.category_display}</span>
        </div>
        <p className="mb-3 line-clamp-2 text-sm text-gray-500">{ticket.description}</p>
        <div className="space-y-2 border-t border-gray-100 pt-3 text-sm text-gray-700">
          {ticket.branch_name && <Info icon={<Building2 size={14} />} value={ticket.branch_name} />}
          {ticket.site_name && <Info icon={<MapPin size={14} />} value={ticket.site_name} />}
          <Info icon={<User size={14} />} value={ticket.assigned_to_name || "Tayinlanmagan"} />
          <Info icon={<Calendar size={14} />} value={formatDateTime(ticket.created_at)} />
        </div>
      </div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
