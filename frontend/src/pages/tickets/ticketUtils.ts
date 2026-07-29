import type { TicketPriority, TicketStatus } from "../../types/ticket";

export const CATEGORY_OPTIONS = [
  { value: "material_shortage", label: "Material yetishmasligi" },
  { value: "equipment", label: "Texnika kerak" },
  { value: "labor", label: "Ishchi kuchi" },
  { value: "other", label: "Boshqa" },
] as const;

export const PRIORITY_OPTIONS: { value: TicketPriority; label: string }[] = [
  { value: "low", label: "Past" },
  { value: "medium", label: "O'rta" },
  { value: "high", label: "Yuqori" },
  { value: "urgent", label: "Shoshilinch" },
];

export const STATUS_OPTIONS: { value: TicketStatus; label: string }[] = [
  { value: "open", label: "Ochiq" },
  { value: "in_progress", label: "Jarayonda" },
  { value: "resolved", label: "Yechildi" },
  { value: "closed", label: "Yopildi" },
];

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  low: "bg-gray-100 text-gray-500",
  medium: "bg-blue-50 text-blue-600",
  high: "bg-amber-50 text-amber-700",
  urgent: "bg-red-50 text-red-700 font-semibold",
};

export function priorityBadgeClass(priority: string) {
  return PRIORITY_STYLES[priority as TicketPriority] ?? "bg-gray-100 text-gray-500";
}

const STATUS_STYLES: Record<TicketStatus, string> = {
  open: "bg-red-50 text-red-700",
  in_progress: "bg-amber-50 text-amber-700",
  resolved: "bg-lime-50 text-lime-700",
  closed: "bg-green-50 text-green-700",
};

export function statusBadgeClass(status: string) {
  return STATUS_STYLES[status as TicketStatus] ?? "bg-gray-100 text-gray-600";
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
