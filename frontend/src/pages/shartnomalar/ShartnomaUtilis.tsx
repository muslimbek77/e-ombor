export function isExpiringSoon(endDate: string): boolean {
  const end = new Date(endDate).getTime();
  const now = Date.now();
  const daysLeft = (end - now) / (1000 * 60 * 60 * 24);
  return daysLeft > 0 && daysLeft <= 60;
}

export function isExpired(endDate: string): boolean {
  return new Date(endDate).getTime() < Date.now();
}

export function Field({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string | React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 py-3.5 border-b border-gray-100 last:border-0">
      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-gray-400">{icon}</span>
      </div>
      <div className="flex flex-col min-w-0">
        <span className="text-xs text-gray-400 font-medium mb-0.5">
          {label}
        </span>
        <span className="text-gray-800 text-sm font-medium">
          {value ?? "—"}
        </span>
      </div>
    </div>
  );
}
