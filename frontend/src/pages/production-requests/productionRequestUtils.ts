import type { ProductionRequestStatus } from "../../types/productionRequest";

export const STATUS_OPTIONS: { value: ProductionRequestStatus; label: string }[] = [
  { value: "pending", label: "Kutilmoqda" },
  { value: "approved", label: "Tasdiqlandi" },
  { value: "delivered", label: "Yetkazildi" },
  { value: "cancelled", label: "Bekor qilindi" },
];

const STATUS_STYLES: Record<ProductionRequestStatus, string> = {
  pending: "bg-amber-50 text-amber-700",
  approved: "bg-blue-50 text-blue-700",
  delivered: "bg-green-50 text-green-700",
  cancelled: "bg-red-50 text-red-700",
};

export function statusBadgeClass(status: string) {
  return STATUS_STYLES[status as ProductionRequestStatus] ?? "bg-gray-100 text-gray-600";
}

/** Zayavka holati bo'yicha ruxsat etilgan keyingi qadamlar. */
const STATUS_TRANSITIONS: Record<ProductionRequestStatus, ProductionRequestStatus[]> = {
  pending: ["approved", "cancelled"],
  approved: ["delivered", "cancelled"],
  delivered: [],
  cancelled: [],
};

const TRANSITION_LABELS: Record<ProductionRequestStatus, string> = {
  pending: "Kutishga qaytarish",
  approved: "Tasdiqlash",
  delivered: "Yetkazildi deb belgilash",
  cancelled: "Bekor qilish",
};

export function nextStatuses(status: ProductionRequestStatus) {
  return (STATUS_TRANSITIONS[status] ?? []).map((value) => ({ value, label: TRANSITION_LABELS[value] }));
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
