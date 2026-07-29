import type { DocStatus, DocType, WorkflowAction } from "../../types/document";

export const DOC_TYPE_OPTIONS: { value: DocType; label: string }[] = [
  { value: "purchase_request", label: "Xarid so'rovi" },
  { value: "contract", label: "Shartnoma" },
  { value: "invoice", label: "Invoice" },
];

const DOC_TYPE_LABELS: Record<string, string> = Object.fromEntries(DOC_TYPE_OPTIONS.map((option) => [option.value, option.label]));

export function docTypeLabel(docType: string) {
  return DOC_TYPE_LABELS[docType] ?? docType;
}

export const STATUS_FILTERS = [
  { value: "all", label: "Barchasi" },
  { value: "created", label: "Yaratildi" },
  { value: "architecture", label: "Arxitekturada" },
  { value: "ceo", label: "Raisda" },
  { value: "approved", label: "Tasdiqlandi" },
  { value: "contract", label: "Shartnomada" },
  { value: "payment", label: "To'lovda" },
  { value: "delivering", label: "Yetkazilmoqda" },
  { value: "received", label: "Qabul qilindi" },
  { value: "closed", label: "Yopildi" },
  { value: "rejected", label: "Rad etildi" },
] as const;

const STATUS_STYLES: Record<DocStatus, string> = {
  created: "bg-gray-100 text-gray-600",
  architecture: "bg-blue-50 text-blue-600",
  ceo: "bg-blue-50 text-blue-600",
  approved: "bg-lime-50 text-lime-700",
  contract: "bg-amber-50 text-amber-700",
  payment: "bg-amber-50 text-amber-700",
  delivering: "bg-purple-50 text-purple-700",
  received: "bg-green-50 text-green-700",
  closed: "bg-green-50 text-green-700",
  rejected: "bg-red-50 text-red-700",
};

export function statusBadgeClass(status: string) {
  return STATUS_STYLES[status as DocStatus] ?? "bg-gray-100 text-gray-600";
}

const ACTION_LABELS: Record<WorkflowAction, string> = {
  submit: "Yuborish",
  approve: "Tasdiqlash",
  advance: "Keyingi bosqichga o'tkazish",
  close: "Yopish",
  reject: "Rad etish",
  reopen: "Qayta ochish",
};

export function actionLabel(action: WorkflowAction) {
  return ACTION_LABELS[action] ?? action;
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
