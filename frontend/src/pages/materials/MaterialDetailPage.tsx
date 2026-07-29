import {
  ArrowLeft,
  Calendar,
  FileText,
  Layers,
  Pencil,
  Ruler,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import {
  useDeleteMaterial,
  useMaterial,
  useUpdateMaterial,
} from "../../hooks/useMaterials";
import { formatDate } from "../objects/siteUtils";
import { MaterialForm } from "./MaterialForm";

export default function MaterialDetailPage() {
  const { id } = useParams();
  const materialId = Number(id);
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const { data: material, isPending, isError } = useMaterial(materialId);
  const updateMaterial = useUpdateMaterial();
  const deleteMaterial = useDeleteMaterial();
  if (!Number.isInteger(materialId) || materialId < 1)
    return <DetailState>Material ID noto‘g‘ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !material)
    return <DetailState>Materialni yuklashda xatolik yuz berdi.</DetailState>;
  function confirmDelete() {
    deleteMaterial.mutate(material!.id, {
      onSuccess: () => {
        toast.success("Material o‘chirildi.");
        navigate("/materials", { replace: true });
      },
      onError: () => toast.error("Materialni o‘chirib bo‘lmadi."),
    });
  }

  function handleDelete() {
    toast(
      ({ closeToast }) => (
        <div className="text-sm">
          <p className="font-medium text-gray-900">
            “{material!.name}” materialini o‘chirmoqchimisiz?
          </p>
          <div className="mt-3 flex justify-end gap-2">
            <button
              type="button"
              onClick={closeToast}
              className="rounded-lg px-3 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-100"
            >
              Yo‘q
            </button>
            <button
              type="button"
              onClick={() => {
                confirmDelete();
                closeToast?.();
              }}
              className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
            >
              Ha, o‘chirish
            </button>
          </div>
        </div>
      ),
      { autoClose: false, closeOnClick: false, position: "top-center" },
    );
  }
  const details = [
    [<Ruler size={17} />, "O‘lchov birligi", material.unit],
    [<Layers size={17} />, "Kategoriya", material.category],
    [<FileText size={17} />, "Tavsif", material.description || "—"],
    [
      <Calendar size={17} />,
      "Yaratilgan sana",
      formatDate(material.created_at),
    ],
  ];
  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl space-y-5">
        <Link
          to="/materials"
          className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700"
        >
          <ArrowLeft size={16} /> Materiallarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {material.name}
              </h1>
              <p className="mt-1 text-sm text-gray-500">Kod: {material.code}</p>
            </div>
            <div className="flex items-center gap-2">
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
                disabled={deleteMaterial.isPending}
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
              >
                <Trash2 size={15} /> O‘chirish
              </button>
            </div>
          </div>
          {isEditing ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">
                Materialni tahrirlash
              </h2>
              {updateMaterial.isError && (
                <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                  O‘zgarishlarni saqlab bo‘lmadi.
                </p>
              )}
              <MaterialForm
                key={material.id}
                initialMaterial={material}
                submitLabel="Saqlash"
                isSubmitting={updateMaterial.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) =>
                  updateMaterial.mutate(
                    { materialId: material.id, payload },
                    { onSuccess: () => setIsEditing(false) },
                  )
                }
              />
            </>
          ) : (
            <dl className="grid gap-4 sm:grid-cols-2">
              {details.map(([icon, label, value]) => (
                <div
                  key={String(label)}
                  className="flex gap-3 rounded-xl bg-gray-50 p-4"
                >
                  <span className="mt-0.5 text-gray-400">{icon}</span>
                  <div>
                    <dt className="text-xs font-medium text-gray-500">
                      {label}
                    </dt>
                    <dd className="mt-1 text-sm font-semibold text-gray-800">
                      {value}
                    </dd>
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
  return (
    <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">
      {children}
    </main>
  );
}
