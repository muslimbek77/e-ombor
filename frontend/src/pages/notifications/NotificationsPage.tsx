import { Check, CheckCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from "../../hooks/useNotifications";
import type { Notification } from "../../types/notification";
import { formatDate } from "../objects/siteUtils";

/** `related_type` -> sahifa marshruti. Mos kelmasa bosish hech qayerga olib bormaydi. */
const RELATED_TYPE_ROUTES: Record<string, string> = {
  document: "/documents",
  ticket: "/tickets",
  invoice: "/invoices",
  inventory: "/inventory",
};

function notificationHref(notification: Notification): string | null {
  if (!notification.related_type || notification.related_id == null) return null;
  const base = RELATED_TYPE_ROUTES[notification.related_type];
  return base ? `${base}/${notification.related_id}` : null;
}

export default function NotificationsPage() {
  const { data: notifications = [], isPending, isError } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const navigate = useNavigate();
  const hasUnread = notifications.some((notification) => !notification.is_read);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) markRead.mutate(notification.id);
    const href = notificationHref(notification);
    if (href) navigate(href);
  };

  return <main className="min-h-full bg-gray-50 p-6"><div className="space-y-5"><header className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold text-gray-900">Bildirishnomalar</h1><p className="mt-0.5 text-sm text-gray-400">{isPending ? "Yuklanmoqda..." : `${notifications.length} ta bildirishnoma`}</p></div><button type="button" onClick={() => markAllRead.mutate()} disabled={!hasUnread || markAllRead.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"><CheckCheck size={16} /> Hammasini o‘qildi</button></header>{isPending && <PageState>Yuklanmoqda...</PageState>}{isError && <PageState className="text-red-500">Bildirishnomalarni yuklashda xatolik yuz berdi</PageState>}{!isPending && !isError && notifications.length === 0 && <PageState>Bildirishnomalar topilmadi</PageState>}{!isPending && !isError && notifications.length > 0 && <section className="space-y-3" aria-label="Bildirishnomalar ro‘yxati">{notifications.map((notification) => { const clickable = notificationHref(notification) !== null; return <article key={notification.id} onClick={clickable ? () => handleNotificationClick(notification) : undefined} className={`flex items-start gap-3 rounded-2xl bg-white p-4 shadow-sm ${!notification.is_read ? "bg-green-50/60" : ""} ${clickable ? "cursor-pointer hover:bg-gray-50" : ""}`}><span className={`mt-1.5 size-2.5 shrink-0 rounded-full ${!notification.is_read ? "bg-green-500" : "bg-transparent"}`} /><div className="min-w-0 flex-1"><h2 className="text-sm font-bold text-gray-900">{notification.title}</h2><p className="mt-1 text-sm text-gray-600">{notification.message}</p><p className="mt-2 text-xs text-gray-400">{formatDate(notification.created_at)}</p></div>{!notification.is_read && <button type="button" onClick={(event) => { event.stopPropagation(); markRead.mutate(notification.id); }} disabled={markRead.isPending} className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"><Check size={14} /> O‘qildi</button>}</article>; })}</section>}</div></main>;
}

function PageState({ children, className = "" }: { children: React.ReactNode; className?: string }) { return <div className={`flex h-40 items-center justify-center text-sm text-gray-400 ${className}`}>{children}</div>; }
