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
  { value: "revision", label: "Tuzatishda" },
  { value: "architecture", label: "Arxitekturada" },
  { value: "ceo", label: "Raisda" },
  { value: "procurement", label: "Xaridlarda" },
  { value: "anticorruption", label: "Nazoratda" },
  { value: "accountant", label: "Buxgalteriyada" },
  { value: "delivering", label: "Yetkazilmoqda" },
  { value: "received", label: "Qabul qilindi" },
  { value: "closed", label: "Yopildi" },
  { value: "rejected", label: "Rad etildi" },
] as const;

/**
 * Hujjat faqat shu holatlarda tahrirlanadi — manba `backend/api/workflow.py`
 * (`EDITABLE_STATUSES`). Zanjir boshlangach hujjat muzlaydi: server boshqa
 * holatda 409 qaytaradi. Tuzatish yo'li — `return` (yoki `reject`), so'ng
 * tuzatib qayta `submit`.
 */
export const EDITABLE_STATUSES: DocStatus[] = ["created", "revision", "rejected"];

export function isDocumentEditable(status: DocStatus) {
  return EDITABLE_STATUSES.includes(status);
}

/**
 * Izohsiz yuborilmaydigan amallar — server ikkalasida ham 400 qaytaradi
 * (`workflow.py: COMMENT_REQUIRED_ACTIONS`).
 */
export const COMMENT_REQUIRED_ACTIONS: WorkflowAction[] = ["reject", "return"];

export function requiresComment(action: WorkflowAction) {
  return COMMENT_REQUIRED_ACTIONS.includes(action);
}

const STATUS_STYLES: Record<DocStatus, string> = {
  created: "bg-gray-100 text-gray-600",
  // Tuzatishda — hujjat egasidan harakat kutayotgan yagona holat, shuning
  // uchun ro'yxatda ajralib turadi.
  revision: "bg-yellow-50 text-yellow-700",
  architecture: "bg-blue-50 text-blue-600",
  ceo: "bg-blue-50 text-blue-600",
  procurement: "bg-lime-50 text-lime-700",
  // Nazorat bosqichi ataylab boshqa rangda — zanjirdagi tekshiruv nuqtasi
  // ro'yxatda ko'zga tashlanib tursin.
  anticorruption: "bg-orange-50 text-orange-700",
  accountant: "bg-amber-50 text-amber-700",
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
  // "Rad etildi" emas, "tuzatib qayta yuboring" — farq shu ikki so'zda.
  return: "Tuzatishga qaytarish",
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
