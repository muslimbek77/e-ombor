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

export function actionLabel(action: string) {
  return action.replaceAll("_", " ");
}
