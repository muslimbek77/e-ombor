export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function actionBadgeClass(action: string) {
  if (action.includes("unarchived")) return "bg-blue-50 text-blue-700";
  if (action.includes("deleted") || action.includes("archived") || action.includes("rejected")) return "bg-red-50 text-red-700";
  if (action.includes("created") || action.includes("approved")) return "bg-green-50 text-green-700";
  if (action.includes("updated") || action.includes("changed") || action.includes("adjusted")) return "bg-blue-50 text-blue-700";
  if (action.includes("uploaded")) return "bg-purple-50 text-purple-700";
  return "bg-gray-100 text-gray-600";
}

/**
 * Backend `create_audit_log(...)` ga uzatadigan amal nomlari (`api/views.py`).
 * Yangi amal qo'shilsa shu yerga ham qo'shing — aks holda jurnalda inglizcha
 * kalit ko'rinadi (tushib qolgani bilinsin uchun fallback o'chirilmagan).
 */
const ACTION_LABELS: Record<string, string> = {
  document_created: "Hujjat yaratildi",
  document_workflow_changed: "Hujjat holati o'zgardi",
  document_archived: "Hujjat arxivlandi",
  document_unarchived: "Hujjat arxivdan chiqarildi",
  document_file_uploaded: "Hujjatga fayl yuklandi",
  contract_created: "Shartnoma yaratildi",
  contract_updated: "Shartnoma tahrirlandi",
  purchase_order_created: "Xarid buyurtmasi yaratildi",
  purchase_order_updated: "Xarid buyurtmasi tahrirlandi",
  purchase_order_deleted: "Xarid buyurtmasi o'chirildi",
  payment_created: "To'lov qayd etildi",
  inventory_created: "Inventar yozuvi yaratildi",
  inventory_adjusted: "Qoldiq korrektirovka qilindi",
  stock_movement_created: "Ombor harakati qayd etildi",
  ticket_created: "Murojaat yaratildi",
  user_created: "Foydalanuvchi yaratildi",
  user_updated: "Foydalanuvchi tahrirlandi",
  user_deleted: "Foydalanuvchi o'chirildi",
  password_changed: "Parol o'zgartirildi",
  // `seed_demo_data` yozadigan demo yozuvlari.
  supplier_added: "Yetkazib beruvchi qo'shildi",
  site_created: "Qurilish obyekti yaratildi",
  request_created: "Zayavka yaratildi",
  contract_signed: "Shartnoma imzolandi",
  inventory_updated: "Inventar yangilandi",
  seed_demo_data: "Demo ma'lumotlar yuklandi",
};

export function actionLabel(action: string) {
  return ACTION_LABELS[action] ?? action.replaceAll("_", " ");
}
