import { ArrowLeft, Calendar, ClipboardList, Hash, MapPin, Pencil, RefreshCw, User } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useProductionRequest, useUpdateProductionRequest, useUpdateProductionRequestStatus } from "../../hooks/useProductionRequests";
import { PRODUCTION_REQUEST_STATUS_ROLES, useHasRole } from "../../lib/permissions";
import { useAuthStore } from "../../stores/authStore";
import { ProductionRequestForm } from "./ProductionRequestForm";
import { formatDateTime, nextStatuses, statusBadgeClass } from "./productionRequestUtils";
import type { ProductionRequest, ProductionRequestUpdatePayload } from "../../types/productionRequest";

export default function ProductionRequestDetailPage() {
  const { id } = useParams();
  const requestId = Number(id);
  const [isEditing, setIsEditing] = useState(false);
  const { data: request, isPending, isError } = useProductionRequest(requestId);
  const updateRequest = useUpdateProductionRequest();
  const updateStatus = useUpdateProductionRequestStatus();
  const currentUser = useAuthStore((state) => state.user);
  const canManageStatus = useHasRole(PRODUCTION_REQUEST_STATUS_ROLES);

  if (!Number.isInteger(requestId) || requestId < 1) return <DetailState>Zayavka ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !request) return <DetailState>Zayavkani yuklashda xatolik yuz berdi.</DetailState>;

  const isAuthor = request.created_by === currentUser?.id;
  const canEdit = canManageStatus || (isAuthor && request.status === "pending");
  const transitions = canManageStatus ? nextStatuses(request.status) : [];

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/production-requests" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Zayavkalarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{request.title}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(request.status)}`}>{request.status_display}</span>
                <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{request.request_number}</span>
              </div>
            </div>
            {canEdit && (
              <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
              </button>
            )}
          </div>
          {(updateRequest.isError || updateStatus.isError) && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
          {isEditing && canEdit ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Zayavkani tahrirlash</h2>
              <ProductionRequestForm
                initialRequest={request}
                canManageStatus={canManageStatus}
                submitLabel="Saqlash"
                isSubmitting={updateRequest.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateRequest.mutate({ requestId: request.id, payload: payload as ProductionRequestUpdatePayload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <RequestInformation request={request} />
          )}
        </section>

        {!isEditing && canManageStatus && (
          <section className="rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="mb-1 flex items-center gap-2 text-lg font-bold text-gray-900"><RefreshCw size={17} className="text-gray-400" /> Holat o'zgarishi</h2>
            <p className="mb-4 text-sm text-gray-500">
              {transitions.length > 0 ? "Zayavkani keyingi bosqichga o'tkazing." : "Bu zayavka yakuniy holatda — boshqa o'zgarish mumkin emas."}
            </p>
            <div className="flex flex-wrap gap-2">
              {transitions.map((transition) => (
                <button
                  key={transition.value}
                  type="button"
                  disabled={updateStatus.isPending}
                  onClick={() => updateStatus.mutate({ requestId: request.id, status: transition.value })}
                  className={`rounded-xl px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 ${transition.value === "cancelled" ? "bg-red-600 hover:bg-red-700" : "bg-green-600 hover:bg-green-700"}`}
                >
                  {updateStatus.isPending ? "Saqlanmoqda..." : transition.label}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function RequestInformation({ request }: { request: ProductionRequest }) {
  const details = [
    [<ClipboardList size={17} />, "Tavsif", request.description || "—"],
    [<Hash size={17} />, "Zayavka raqami", request.request_number],
    [<MapPin size={17} />, "Obyekt", request.site_name || "—"],
    [<User size={17} />, "Yaratgan xodim", request.created_by_name || "Noma'lum"],
    [<Calendar size={17} />, "Yaratilgan sana", formatDateTime(request.created_at)],
    [<Calendar size={17} />, "Yangilangan sana", formatDateTime(request.updated_at)],
  ] as const;

  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      {details.map(([icon, label, value]) => (
        <div key={label} className="flex gap-3 rounded-xl bg-gray-50 p-4">
          <span className="mt-0.5 text-gray-400">{icon}</span>
          <div>
            <dt className="text-xs font-medium text-gray-500">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
          </div>
        </div>
      ))}
    </dl>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
