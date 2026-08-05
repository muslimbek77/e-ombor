import { ArrowLeft, Building2, MapPin, Pencil, Route, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAddress, useDeleteAddress, useUpdateAddress } from "../../hooks/useAddresses";
import { AddressForm } from "./AddressForm";
import { REFERENCE_DATA_ROLES, useHasRole } from "../../lib/permissions";

export default function AddressDetailPage() {
  const { id } = useParams();
  const addressId = Number(id);
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const { data: address, isPending, isError } = useAddress(addressId);
  const updateAddress = useUpdateAddress();
  const deleteAddress = useDeleteAddress();
  const canManageAddresses = useHasRole(REFERENCE_DATA_ROLES);

  if (!Number.isInteger(addressId) || addressId < 1) return <DetailState>Manzil ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !address) return <DetailState>Manzilni yuklashda xatolik yuz berdi.</DetailState>;

  function handleDelete() {
    if (!address) return;
    if (!window.confirm(`"${address.city}" manzilini o'chirmoqchimisiz?`)) return;
    deleteAddress.mutate(address.id, { onSuccess: () => navigate("/addresses", { replace: true }) });
  }

  const details = [
    [<Building2 size={17} />, "Tuman", address.district || "—"],
    [<Route size={17} />, "Ko'cha", address.street || "—"],
    [<MapPin size={17} />, "Bino", address.building || "—"],
  ] as const;

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-5">
        <Link to="/addresses" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Manzillarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{address.city}</h1>
            </div>
            <div className="flex items-center gap-2">
              {canManageAddresses && (
                <>
                  <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                    <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
                  </button>
                  <button type="button" onClick={handleDelete} disabled={deleteAddress.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                    <Trash2 size={15} /> O'chirish
                  </button>
                </>
              )}
            </div>
          </div>

          {deleteAddress.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Manzilni o'chirib bo'lmadi.</p>}

          {isEditing ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Manzilni tahrirlash</h2>
              {updateAddress.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
              <AddressForm
                key={address.id}
                initialAddress={address}
                submitLabel="Saqlash"
                isSubmitting={updateAddress.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateAddress.mutate({ addressId: address.id, payload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <dl className="grid gap-4 sm:grid-cols-2">
              {details.map(([icon, label, value]) => (
                <div key={String(label)} className="flex gap-3 rounded-xl bg-gray-50 p-4">
                  <span className="mt-0.5 text-gray-400">{icon}</span>
                  <div>
                    <dt className="text-xs font-medium text-gray-500">{label}</dt>
                    <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
                  </div>
                </div>
              ))}
            </dl>
          )}
        </section>
      </div>
    </main>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
