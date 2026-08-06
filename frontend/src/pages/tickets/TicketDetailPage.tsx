import { ArrowLeft, Building2, Calendar, MapPin, MessageSquare, Pencil, Tag, User } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTicket, useUpdateTicket } from "../../hooks/useTickets";
import { TICKET_MANAGE_ROLES, useHasRole } from "../../lib/permissions";
import { useAuthStore } from "../../stores/authStore";
import { TicketForm } from "./TicketForm";
import { formatDateTime, priorityBadgeClass, statusBadgeClass } from "./ticketUtils";
import type { TicketUpdatePayload } from "../../types/ticket";

export default function TicketDetailPage() {
  const { id } = useParams();
  const ticketId = Number(id);
  const [isEditing, setIsEditing] = useState(false);
  const { data: ticket, isPending, isError } = useTicket(ticketId);
  const updateTicket = useUpdateTicket();
  const currentUser = useAuthStore((state) => state.user);
  const canManageFields = useHasRole(TICKET_MANAGE_ROLES);

  if (!Number.isInteger(ticketId) || ticketId < 1) return <DetailState>Murojaat ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !ticket) return <DetailState>Murojaatni yuklashda xatolik yuz berdi.</DetailState>;

  const isAuthor = ticket.created_by === currentUser?.id;
  const canEdit = canManageFields || isAuthor;

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/tickets" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Murojaatlarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{ticket.title}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(ticket.status)}`}>{ticket.status_display}</span>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${priorityBadgeClass(ticket.priority)}`}>{ticket.priority_display}</span>
                <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{ticket.category_display}</span>
              </div>
            </div>
            {canEdit && (
              <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
              </button>
            )}
          </div>
          {updateTicket.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
          {isEditing && canEdit ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Murojaatni tahrirlash</h2>
              <TicketForm
                initialTicket={ticket}
                canManageFields={canManageFields}
                submitLabel="Saqlash"
                isSubmitting={updateTicket.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateTicket.mutate({ ticketId: ticket.id, payload: payload as TicketUpdatePayload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <TicketInformation ticket={ticket} />
          )}
        </section>
      </div>
    </main>
  );
}

function TicketInformation({ ticket }: { ticket: NonNullable<ReturnType<typeof useTicket>["data"]> }) {
  const details = [
    [<Tag size={17} />, "Tavsif", ticket.description],
    [<Building2 size={17} />, "Filial", ticket.branch_name || "—"],
    [<MapPin size={17} />, "Obyekt", ticket.site_name || "—"],
    [<User size={17} />, "Mas'ul xodim", ticket.assigned_to_name || "Tayinlanmagan"],
    [<Calendar size={17} />, "Yaratilgan sana", formatDateTime(ticket.created_at)],
  ] as const;

  return (
    <div className="space-y-4">
      <dl className="grid gap-4 sm:grid-cols-2">
        {details.map(([icon, label, value]) => (
          <div key={label} className="flex gap-3 rounded-xl bg-gray-50 p-4">
            <span className="mt-0.5 text-gray-400">{icon}</span>
            <div>
              <dt className="text-xs font-medium text-gray-500">{label}</dt>
              <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
            </div>
          </div>
        ))}
      </dl>
      {ticket.response && (
        <div className="flex gap-3 rounded-xl bg-green-50 p-4">
          <span className="mt-0.5 text-green-500"><MessageSquare size={17} /></span>
          <div>
            <dt className="text-xs font-medium text-green-700">Javob</dt>
            <dd className="mt-1 text-sm font-semibold text-green-900">{ticket.response}</dd>
          </div>
        </div>
      )}
    </div>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
