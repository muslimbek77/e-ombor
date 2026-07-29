import { ArrowLeft, AtSign, MapPin, Pencil, Phone, Trash2, UserRound } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useDeleteSupplier, useSupplier, useUpdateSupplier } from "../../hooks/useSuppliers";
import { formatDate } from "../objects/siteUtils";
import { SupplierForm } from "./SupplierForm";

export default function SupplierDetailPage() {
  const { id } = useParams();
  const supplierId = Number(id);
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const { data: supplier, isPending, isError } = useSupplier(supplierId);
  const updateSupplier = useUpdateSupplier();
  const deleteSupplier = useDeleteSupplier();

  if (!Number.isInteger(supplierId) || supplierId < 1) return <DetailState>Supplier ID noto‘g‘ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !supplier) return <DetailState>Supplierni yuklashda xatolik yuz berdi.</DetailState>;

  function handleDelete() {
    if (!window.confirm(`“${supplier.name}” supplierini o‘chirmoqchimisiz?`)) return;
    deleteSupplier.mutate(supplier.id, { onSuccess: () => navigate("/suppliers", { replace: true }) });
  }

  return (
    <main className="min-h-full bg-gray-50 p-6"><div className="mx-auto max-w-4xl space-y-5"><Link to="/suppliers" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700"><ArrowLeft size={16} /> Supplierlarga qaytish</Link><section className="rounded-2xl bg-white p-6 shadow-sm"><div className="mb-6 flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-bold text-gray-900">{supplier.name}</h1><p className="mt-1 text-sm text-gray-500">Kod: {supplier.code}</p></div><div className="flex items-center gap-2"><span className={`rounded-full px-3 py-1.5 text-sm font-semibold ${supplier.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>{supplier.is_active ? "Faol" : "Nofaol"}</span><button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"><Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}</button><button type="button" onClick={handleDelete} disabled={deleteSupplier.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"><Trash2 size={15} /> O‘chirish</button></div></div>{deleteSupplier.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Supplierni o‘chirib bo‘lmadi.</p>}{isEditing ? <><h2 className="mb-4 text-lg font-bold text-gray-900">Supplierni tahrirlash</h2>{updateSupplier.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O‘zgarishlarni saqlab bo‘lmadi.</p>}<SupplierForm key={supplier.id} initialSupplier={supplier} submitLabel="Saqlash" isSubmitting={updateSupplier.isPending} onCancel={() => setIsEditing(false)} onSubmit={(payload) => updateSupplier.mutate({ supplierId: supplier.id, payload }, { onSuccess: () => setIsEditing(false) })} /></> : <SupplierInformation supplier={supplier} />}</section></div></main>
  );
}

function SupplierInformation({ supplier }: { supplier: NonNullable<ReturnType<typeof useSupplier>["data"]> }) {
  const details = [[<UserRound size={17} />, "Mas’ul shaxs", supplier.contact_person], [<Phone size={17} />, "Telefon", supplier.phone], [<AtSign size={17} />, "Email", supplier.email], [<MapPin size={17} />, "Manzil", supplier.address], [<UserRound size={17} />, "Yaratilgan sana", formatDate(supplier.created_at)]];
  return <dl className="grid gap-4 sm:grid-cols-2">{details.map(([icon, label, value]) => <div key={String(label)} className="flex gap-3 rounded-xl bg-gray-50 p-4"><span className="mt-0.5 text-gray-400">{icon}</span><div><dt className="text-xs font-medium text-gray-500">{label}</dt><dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd></div></div>)}</dl>;
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
