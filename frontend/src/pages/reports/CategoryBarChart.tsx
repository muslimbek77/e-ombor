interface CategoryBarChartProps {
  title: string;
  icon: React.ReactNode;
  order: readonly { value: string; label: string }[];
  counts: { value: string; total: number }[];
}

export function CategoryBarChart({ title, icon, order, counts }: CategoryBarChartProps) {
  const totalsByValue = new Map(counts.map((count) => [count.value, count.total]));
  const rows = order.map((option) => ({ label: option.label, total: totalsByValue.get(option.value) ?? 0 }));
  const max = Math.max(1, ...rows.map((row) => row.total));

  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-900">{icon} {title}</h2>
      <div className="space-y-2.5">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center gap-3">
            <span className="w-32 shrink-0 text-xs leading-tight text-gray-500">{row.label}</span>
            <div className="h-2.5 flex-1 rounded-r bg-gray-100">
              <div className="h-2.5 rounded-r bg-green-600" style={{ width: `${(row.total / max) * 100}%` }} />
            </div>
            <span className="w-6 shrink-0 text-right text-xs font-semibold text-gray-700">{row.total}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
