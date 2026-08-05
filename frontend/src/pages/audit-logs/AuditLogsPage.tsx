import { Search } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { useAuditLogs } from "../../hooks/useAuditLogs";
import { actionBadgeClass, actionLabel, formatDateTime } from "./auditLogUtils";

const ALL = "all";

export default function AuditLogsPage() {
  const [query, setQuery] = useState("");
  const [actionFilter, setActionFilter] = useState(ALL);
  const [userFilter, setUserFilter] = useState(ALL);
  const deferredQuery = useDeferredValue(query);
  const { data: logs = [], isPending, isError } = useAuditLogs();

  const actions = useMemo(() => [...new Set(logs.map((log) => log.action))].sort(), [logs]);
  const users = useMemo(() => [...new Set(logs.map((log) => log.user_name).filter((name): name is string => Boolean(name)))].sort(), [logs]);

  const filteredLogs = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLocaleLowerCase();
    return logs.filter((log) => {
      const matchesAction = actionFilter === ALL || log.action === actionFilter;
      const matchesUser = userFilter === ALL || log.user_name === userFilter;
      const matchesQuery = !normalizedQuery || [actionLabel(log.action), log.model_name, log.object_label, log.user_name, log.ip_address].some((value) => (value ?? "").toLocaleLowerCase().includes(normalizedQuery));
      return matchesAction && matchesUser && matchesQuery;
    });
  }, [deferredQuery, actionFilter, userFilter, logs]);

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="space-y-5">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Audit jurnali</h1>
            <p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${filteredLogs.length} ta yozuv`}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative">
              <span className="sr-only">Jurnalni qidirish</span>
              <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400" />
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Qidirish..." className="w-48 rounded-xl border border-gray-200 bg-white py-2 pr-3 pl-9 text-sm focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30" />
            </label>
            <select value={actionFilter} onChange={(event) => setActionFilter(event.target.value)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30">
              <option value={ALL}>Barcha amallar</option>
              {actions.map((action) => <option key={action} value={action}>{actionLabel(action)}</option>)}
            </select>
            <select value={userFilter} onChange={(event) => setUserFilter(event.target.value)} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-500/30">
              <option value={ALL}>Barcha foydalanuvchilar</option>
              {users.map((name) => <option key={name} value={name}>{name}</option>)}
            </select>
          </div>
        </header>

        {isPending && <PageState>Yuklanmoqda...</PageState>}
        {isError && <PageState className="text-red-500">Audit jurnalini yuklashda xatolik yuz berdi</PageState>}
        {!isPending && !isError && filteredLogs.length === 0 && <PageState>Yozuvlar topilmadi</PageState>}
        {!isPending && !isError && filteredLogs.length > 0 && (
          <section className="overflow-x-auto rounded-2xl bg-white shadow-sm" aria-label="Audit jurnali ro'yxati">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-semibold tracking-wide text-gray-400 uppercase">
                  <th className="px-4 py-3">Vaqt</th>
                  <th className="px-4 py-3">Foydalanuvchi</th>
                  <th className="px-4 py-3">Amal</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Obyekt</th>
                  <th className="px-4 py-3">IP manzil</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/60">
                    <td className="px-4 py-3 whitespace-nowrap text-gray-500">{formatDateTime(log.created_at)}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{log.user_name ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${actionBadgeClass(log.action)}`}>{actionLabel(log.action)}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{log.model_name}</td>
                    <td className="px-4 py-3 text-gray-600">{log.object_label ?? (log.object_id != null ? `#${log.object_id}` : "—")}</td>
                    <td className="px-4 py-3 text-gray-500">{log.ip_address ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </div>
    </main>
  );
}

function PageState({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`flex h-40 items-center justify-center text-sm text-gray-400 ${className}`}>{children}</div>;
}
