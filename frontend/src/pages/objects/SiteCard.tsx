import { Building2, Calendar, HardHat, MapPin, Tag, Wallet } from "lucide-react";
import { Link } from "react-router-dom";
import type { Site } from "../../types/site";
import { formatBudget, formatDate, getStatusStyle } from "./siteUtils";

interface SiteCardProps {
  site: Site;
}

export function SiteCard({ site }: SiteCardProps) {
  const statusStyle = getStatusStyle(site.status);

  return (
    <Link
      to={`/objects/${site.id}`}
      className="block overflow-hidden rounded-2xl bg-white transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500"
      style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
    >
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />

      <div className="px-5 py-4">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-base leading-tight font-bold text-gray-900">{site.name}</h2>
            <p className="mt-1 flex items-center gap-1 text-xs font-medium text-gray-400">
              <Tag size={11} />
              {site.code}
            </p>
          </div>
          <span
            className="inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-semibold"
            style={statusStyle}
          >
            {site.status_display}
          </span>
        </div>

        <div className="space-y-2.5 border-t border-gray-100 pt-2">
          <SiteDetail icon={<Building2 size={14} />} value={site.branch_name} />
          <SiteDetail icon={<MapPin size={14} />} value={site.address} alignStart />
          <SiteDetail icon={<HardHat size={14} />} value={site.prorab_name} />
          <SiteDetail icon={<Wallet size={14} />} value={formatBudget(site.budget)} emphasized />
          <SiteDetail icon={<Calendar size={12} />} value={formatDate(site.created_at)} muted />
        </div>
      </div>
    </Link>
  );
}

interface SiteDetailProps {
  icon: React.ReactNode;
  value: string;
  alignStart?: boolean;
  emphasized?: boolean;
  muted?: boolean;
}

function SiteDetail({ icon, value, alignStart, emphasized, muted }: SiteDetailProps) {
  return (
    <div className={`flex gap-2.5 ${alignStart ? "items-start" : "items-center"} ${muted ? "pt-1 text-xs text-gray-400" : "text-sm text-gray-700"}`}>
      <span className={`shrink-0 text-gray-400 ${alignStart ? "mt-0.5" : ""}`}>{icon}</span>
      <span className={emphasized ? "font-semibold text-gray-800" : ""}>{value}</span>
    </div>
  );
}
