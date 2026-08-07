import { Archive, Building2, Calendar, Clock, Hash, Wallet } from "lucide-react";
import { Link } from "react-router-dom";
import type { AppDocument } from "../../types/document";
import { formatBudget, formatDate } from "../objects/siteUtils";
import { daysSince, docTypeLabel, isWaitingStatus, statusBadgeClass, waitingBadgeClass, waitingLabel } from "./documentUtils";

export function DocumentCard({ document }: { document: AppDocument }) {
  const waitingDays = isWaitingStatus(document.status) ? daysSince(document.updated_at) : null;
  return (
    <Link to={`/documents/${document.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="min-w-0 truncate text-base font-bold text-gray-900">{document.title}</h2>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(document.status)}`}>{document.status_display}</span>
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{docTypeLabel(document.doc_type)}</span>
          {document.is_archived && <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-500"><Archive size={11} /> Arxivlangan</span>}
          {waitingDays !== null && <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${waitingBadgeClass(waitingDays)}`}><Clock size={11} /> {waitingLabel(waitingDays)}</span>}
        </div>
        <div className="space-y-2 border-t border-gray-100 pt-3 text-sm text-gray-700">
          <Info icon={<Hash size={14} />} value={document.doc_number} />
          {document.branch_name && <Info icon={<Building2 size={14} />} value={document.branch_name} />}
          <Info icon={<Calendar size={14} />} value={formatDate(document.created_at)} />
          {Number(document.total_amount) > 0 && <Info icon={<Wallet size={14} />} value={formatBudget(document.total_amount)} />}
        </div>
      </div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span>{value}</span></div>;
}
