export function formatBudget(value: string): string {
  const amount = Number(value);

  return Number.isNaN(amount)
    ? value
    : `${new Intl.NumberFormat("uz-UZ").format(amount)} so'm`;
}

export function formatDate(value?: string | null): string {
  if (!value) return "—";

  const date = new Date(value);

  if (isNaN(date.getTime())) return "—";

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}.${month}.${day}`;
}

export function getStatusStyle(status: string) {
  const styles: Record<string, { background: string; color: string }> = {
    active: { background: "#dcfce7", color: "#15803d" },
    paused: { background: "#fef9c3", color: "#854d0e" },
    completed: { background: "#eff6ff", color: "#1d4ed8" },
  };

  return styles[status] ?? { background: "#f3f4f6", color: "#6b7280" };
}
