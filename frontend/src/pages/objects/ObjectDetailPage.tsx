import {
  ArrowLeft,
  Building2,
  Calendar,
  HardHat,
  MapPin,
  Pencil,
  Trash2,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useDeleteSite, useSite, useUpdateSite } from "../../hooks/useObjects";
import { formatBudget, formatDate, getStatusStyle } from "./siteUtils";
import { SiteForm } from "./SiteForm";

export default function ObjectDetailPage() {
  const { id } = useParams();
  const siteId = Number(id);
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const { data: site, isPending, isError } = useSite(siteId);
  const updateSite = useUpdateSite();
  const deleteSite = useDeleteSite();

  if (!Number.isInteger(siteId) || siteId < 1)
    return <DetailState>Obyekt ID noto‘g‘ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !site)
    return <DetailState>Obyektni yuklashda xatolik yuz berdi.</DetailState>;

  const statusStyle = getStatusStyle(site.status);

  function handleDelete() {
    if (!window.confirm(`“${site!.name}” obyektini o‘chirmoqchimisiz?`)) return;
    deleteSite.mutate(site!.id, {
      onSuccess: () => navigate("/objects", { replace: true }),
    });
  }

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-5">
        <Link
          to="/objects"
          className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700"
        >
          <ArrowLeft size={16} /> Obyektlarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{site.name}</h1>
              <p className="mt-1 text-sm text-gray-500">Kod: {site.code}</p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="rounded-full px-3 py-1.5 text-sm font-semibold"
                style={statusStyle}
              >
                {site.status_display}
              </span>
              <button
                type="button"
                onClick={() => setIsEditing((value) => !value)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              >
                <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleteSite.isPending}
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
              >
                <Trash2 size={15} /> O‘chirish
              </button>
            </div>
          </div>
          {deleteSite.isError && (
            <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
              Obyektni o‘chirib bo‘lmadi.
            </p>
          )}
          {isEditing ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">
                Obyektni tahrirlash
              </h2>
              {updateSite.isError && (
                <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                  O‘zgarishlarni saqlab bo‘lmadi.
                </p>
              )}
              <SiteForm
                initialSite={site}
                submitLabel="Saqlash"
                isSubmitting={updateSite.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) =>
                  updateSite.mutate(
                    { siteId: site.id, payload },
                    { onSuccess: () => setIsEditing(false) },
                  )
                }
              />
            </>
          ) : (
            <SiteInformation site={site} />
          )}
        </section>
      </div>
    </main>
  );
}

function SiteInformation({
  site,
}: {
  site: NonNullable<ReturnType<typeof useSite>["data"]>;
}) {
  const details = [
    [<Building2 size={17} />, "Filial", site.branch_name],
    [<MapPin size={17} />, "Manzil", site.address],
    [<HardHat size={17} />, "Prorab", site.prorab_name],
    [<Wallet size={17} />, "Byudjet", formatBudget(site.budget)],
    [<Calendar size={17} />, "Yaratilgan sana", formatDate(site.created_at)],
  ];
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {details.map(([icon, label, value]) => (
        <div
          key={String(label)}
          className="flex gap-3 rounded-xl bg-gray-50 p-4"
        >
          <span className="mt-0.5 text-gray-400">{icon}</span>
          <div>
            <dt className="text-xs font-medium text-gray-500">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-800">
              {value}
            </dd>
          </div>
        </div>
      ))}
    </dl>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">
      {children}
    </main>
  );
}
