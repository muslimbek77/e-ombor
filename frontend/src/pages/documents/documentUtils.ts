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
export const COMMENT_REQUIRED_ACTIONS: WorkflowAction[] = ["reject", "return", "send_back"];

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

/**
 * Kimningdir qarorini kutayotgan holatlar — muallif emas, boshqa rol
 * navbatda. `created`/`revision` bu yerga kirmaydi: u yerda hujjat
 * muallifning o'zida, "kutish" degani boshqa narsa anglatadi.
 */
export const WAITING_STATUSES: DocStatus[] = [
  "architecture",
  "ceo",
  "procurement",
  "anticorruption",
  "accountant",
  "delivering",
  "received",
];

export function isWaitingStatus(status: DocStatus) {
  return WAITING_STATUSES.includes(status);
}

/** `updated_at` dan beri o'tgan to'liq kunlar soni. */
export function daysSince(iso: string): number {
  const diffMs = Date.now() - new Date(iso).getTime();
  return Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
}

/** Kutish qancha cho'zilsa shuncha ko'zga tashlanadi. */
export function waitingBadgeClass(days: number) {
  if (days >= 7) return "bg-red-50 text-red-600";
  if (days >= 3) return "bg-amber-50 text-amber-700";
  return "bg-gray-100 text-gray-500";
}

export function waitingLabel(days: number) {
  if (days === 0) return "Bugundan beri kutmoqda";
  if (days === 1) return "1 kundan beri kutmoqda";
  return `${days} kundan beri kutmoqda`;
}

const ACTION_LABELS: Record<WorkflowAction, string> = {
  submit: "Yuborish",
  approve: "Tasdiqlash",
  advance: "Keyingi bosqichga o'tkazish",
  close: "Yopish",
  reject: "Rad etish",
  // "Rad etildi" emas, "tuzatib qayta yuboring" — farq shu ikki so'zda.
  return: "Tuzatishga qaytarish",
  // "Tuzatishga" emas "bosqichga": hujjat o'zgarmaydi, oldingi bosqich
  // qarorini qayta ko'radi.
  send_back: "Bosqichga qaytarish",
  reopen: "Qayta ochish",
};

export function actionLabel(action: WorkflowAction) {
  return ACTION_LABELS[action] ?? action;
}

/**
 * Faoliyat tarixidagi tasdiqlash yozuvlarining rangi — `reject`/`return`
 * ko'zga tashlanib turishi kerak, chunki ular hujjatni orqaga qaytaradi va
 * izohda nima tuzatilishi kerakligi yozilgan bo'ladi.
 */
const ACTION_CARD_STYLES: Record<WorkflowAction, string> = {
  submit: "border-blue-100 bg-blue-50",
  approve: "border-green-100 bg-green-50",
  advance: "border-purple-100 bg-purple-50",
  close: "border-green-100 bg-green-50",
  reject: "border-red-200 bg-red-50",
  return: "border-yellow-200 bg-yellow-50",
  send_back: "border-orange-200 bg-orange-50",
  reopen: "border-gray-200 bg-gray-50",
};

const ACTION_ICON_STYLES: Record<WorkflowAction, string> = {
  submit: "text-blue-500",
  approve: "text-green-600",
  advance: "text-purple-600",
  close: "text-green-600",
  reject: "text-red-600",
  return: "text-yellow-700",
  send_back: "text-orange-600",
  reopen: "text-gray-500",
};

const ACTION_TITLE_STYLES: Record<WorkflowAction, string> = {
  submit: "text-gray-800",
  approve: "text-gray-800",
  advance: "text-gray-800",
  close: "text-gray-800",
  reject: "text-red-800",
  return: "text-yellow-900",
  send_back: "text-orange-900",
  reopen: "text-gray-800",
};

export function activityCardClass(action?: WorkflowAction) {
  return action ? (ACTION_CARD_STYLES[action] ?? "border-gray-100 bg-gray-50") : "border-gray-100 bg-gray-50";
}

export function activityIconClass(action?: WorkflowAction) {
  return action ? (ACTION_ICON_STYLES[action] ?? "text-gray-400") : "text-gray-400";
}

export function activityTitleClass(action?: WorkflowAction) {
  return action ? (ACTION_TITLE_STYLES[action] ?? "text-gray-800") : "text-gray-800";
}

/** Rad etish/qaytarish sababi — kattaroq va aniqroq ko'rinishi kerak. */
export function activityDetailClass(action?: WorkflowAction) {
  if (action === "reject") return "text-sm font-medium text-red-700";
  if (action === "return") return "text-sm font-medium text-yellow-800";
  if (action === "send_back") return "text-sm font-medium text-orange-800";
  return "text-xs text-gray-500";
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
