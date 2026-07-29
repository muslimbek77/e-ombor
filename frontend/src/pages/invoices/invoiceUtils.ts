import type { PaymentStatus } from "../../types/invoice";

export const STATUS_FILTERS = [
  { value: "all", label: "Barchasi" },
  { value: "unpaid", label: "To'lanmagan" },
  { value: "partial", label: "Qisman to'langan" },
  { value: "paid", label: "To'liq to'langan" },
] as const;

const STATUS_STYLES: Record<PaymentStatus, string> = {
  unpaid: "bg-red-50 text-red-700",
  partial: "bg-amber-50 text-amber-700",
  paid: "bg-green-50 text-green-700",
};

export function statusBadgeClass(status: string) {
  return STATUS_STYLES[status as PaymentStatus] ?? "bg-gray-100 text-gray-600";
}

export function isOverdue(invoice: { due_date: string | null; payment_status: PaymentStatus }) {
  if (!invoice.due_date || invoice.payment_status === "paid") return false;
  return new Date(invoice.due_date).getTime() < Date.now();
}
