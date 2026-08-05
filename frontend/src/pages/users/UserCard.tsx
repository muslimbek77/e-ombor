import { Building2, Mail, Phone } from "lucide-react";
import { Link } from "react-router-dom";
import type { AppUser } from "../../types/user";
import { roleLabel } from "./usersUtils";

export function UserCard({ user }: { user: AppUser }) {
  return (
    <Link to={`/users/${user.id}`} className="block overflow-hidden rounded-2xl bg-white shadow-sm transition-transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-green-500">
      <div className="h-2 bg-linear-to-r from-[#0f1c14] via-[#16a34a] to-[#22c55e]" />
      <div className="p-5">
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="min-w-0 truncate text-base font-bold text-gray-900">{user.full_name}</h2>
          <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${user.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>{user.is_active ? "Faol" : "Faol emas"}</span>
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          {user.roles.map((role) => <span key={role} className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{roleLabel(role)}</span>)}
        </div>
        <div className="space-y-2 border-t border-gray-100 pt-3 text-sm text-gray-700">
          <Info icon={<Mail size={14} />} value={user.email} />
          {user.phone && <Info icon={<Phone size={14} />} value={user.phone} />}
          {user.branch_name && <Info icon={<Building2 size={14} />} value={user.branch_name} />}
        </div>
      </div>
    </Link>
  );
}

function Info({ icon, value }: { icon: React.ReactNode; value: string }) {
  return <div className="flex items-start gap-2.5"><span className="mt-0.5 shrink-0 text-gray-400">{icon}</span><span className="truncate">{value}</span></div>;
}
