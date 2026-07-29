import { useState } from "react";
import type { Ticket, TicketCategory, TicketCreatePayload, TicketPriority, TicketStatus, TicketUpdatePayload } from "../../types/ticket";
import { useSites } from "../../hooks/useObjects";
import { useUsers } from "../../hooks/useUsers";
import { CATEGORY_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS } from "./ticketUtils";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface TicketFormValues {
  title: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  site: string;
  assigned_to: string;
  response: string;
}

function getFormValues(ticket?: Ticket): TicketFormValues {
  if (!ticket) {
    return { title: "", description: "", category: "other", priority: "medium", status: "open", site: "", assigned_to: "", response: "" };
  }
  return {
    title: ticket.title,
    description: ticket.description,
    category: ticket.category,
    priority: ticket.priority,
    status: ticket.status,
    site: ticket.site ? String(ticket.site) : "",
    assigned_to: ticket.assigned_to ? String(ticket.assigned_to) : "",
    response: ticket.response,
  };
}

interface TicketFormProps {
  initialTicket?: Ticket;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: TicketCreatePayload | TicketUpdatePayload) => void;
  onCancel: () => void;
}

export function TicketForm({ initialTicket, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: TicketFormProps) {
  const [values, setValues] = useState<TicketFormValues>(() => getFormValues(initialTicket));
  const { data: sites = [], isPending: isSitesPending } = useSites();
  const { data: users, isPending: isUsersPending, isError: isUsersError } = useUsers();

  function updateField<Key extends keyof TicketFormValues>(key: Key, value: TicketFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const basePayload: TicketCreatePayload = {
      title: values.title,
      description: values.description,
      category: values.category,
      priority: values.priority,
      site: values.site ? Number(values.site) : null,
    };

    if (!initialTicket) {
      onSubmit(basePayload);
      return;
    }

    onSubmit({
      ...basePayload,
      status: values.status,
      assigned_to: values.assigned_to ? Number(values.assigned_to) : null,
      response: values.response,
    } satisfies TicketUpdatePayload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Sarlavha" className="sm:col-span-2">
          <input required value={values.title} onChange={(event) => updateField("title", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Kategoriya">
          <select value={values.category} onChange={(event) => updateField("category", event.target.value as TicketCategory)} className={inputClassName}>
            {CATEGORY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </Field>
        <Field label="Ustuvorlik">
          <select value={values.priority} onChange={(event) => updateField("priority", event.target.value as TicketPriority)} className={inputClassName}>
            {PRIORITY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </Field>
        <Field label="Obyekt (ixtiyoriy)">
          <select disabled={isSitesPending} value={values.site} onChange={(event) => updateField("site", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select>
        </Field>
        {initialTicket && (
          <Field label="Holati">
            <select value={values.status} onChange={(event) => updateField("status", event.target.value as TicketStatus)} className={inputClassName}>
              {STATUS_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </Field>
        )}
        {initialTicket && (
          <Field label="Mas'ul xodim">
            {isUsersError ? (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                Xodimlar ro‘yxatini yuklashga ruxsat yo‘q{initialTicket.assigned_to_name ? ` — joriy: ${initialTicket.assigned_to_name}` : ""}.
              </p>
            ) : (
              <select disabled={isUsersPending} value={values.assigned_to} onChange={(event) => updateField("assigned_to", event.target.value)} className={inputClassName}>
                <option value="">Tayinlanmagan</option>
                {users?.map((user) => <option key={user.id} value={user.id}>{user.full_name}</option>)}
              </select>
            )}
          </Field>
        )}
      </div>
      <Field label="Tavsif">
        <textarea required rows={3} value={values.description} onChange={(event) => updateField("description", event.target.value)} className={inputClassName} />
      </Field>
      {initialTicket && (
        <Field label="Javob">
          <textarea rows={2} value={values.response} onChange={(event) => updateField("response", event.target.value)} className={inputClassName} placeholder="Murojaatga javob yozing..." />
        </Field>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
