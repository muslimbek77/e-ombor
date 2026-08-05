import { ArrowLeft, Building2, Calendar, Mail, Pencil, Phone, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useDeleteUser, useUpdateUser, useUser } from "../../hooks/useUsers";
import { UserForm } from "./UserForm";
import { roleLabel } from "./usersUtils";
import { formatDateTime } from "../tickets/ticketUtils";
import type { UserUpdatePayload } from "../../types/user";

export default function UserDetailPage() {
  const { id } = useParams();
  const userId = Number(id);
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const { data: user, isPending, isError } = useUser(userId);
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  if (!Number.isInteger(userId) || userId < 1) return <DetailState>Foydalanuvchi ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !user) return <DetailState>Foydalanuvchini yuklashda xatolik yuz berdi.</DetailState>;

  function handleDelete() {
    if (!user || !window.confirm(`"${user.full_name}" foydalanuvchisini o'chirmoqchimisiz?`)) return;
    deleteUser.mutate(user.id, { onSuccess: () => navigate("/users", { replace: true }) });
  }

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/users" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Foydalanuvchilarga qaytish
        </Link>
        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{user.full_name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${user.is_active ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>{user.is_active ? "Faol" : "Faol emas"}</span>
                {user.roles.map((role) => <span key={role} className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600">{roleLabel(role)}</span>)}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setIsEditing((value) => !value)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                <Pencil size={15} /> {isEditing ? "Bekor qilish" : "Tahrirlash"}
              </button>
              <button type="button" onClick={handleDelete} disabled={deleteUser.isPending} className="inline-flex items-center gap-1.5 rounded-xl bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                <Trash2 size={15} /> O'chirish
              </button>
            </div>
          </div>
          {updateUser.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">O'zgarishlarni saqlab bo'lmadi.</p>}
          {deleteUser.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Foydalanuvchini o'chirib bo'lmadi.</p>}
          {isEditing ? (
            <>
              <h2 className="mb-4 text-lg font-bold text-gray-900">Foydalanuvchini tahrirlash</h2>
              <UserForm
                initialUser={user}
                submitLabel="Saqlash"
                isSubmitting={updateUser.isPending}
                onCancel={() => setIsEditing(false)}
                onSubmit={(payload) => updateUser.mutate({ userId: user.id, payload: payload as UserUpdatePayload }, { onSuccess: () => setIsEditing(false) })}
              />
            </>
          ) : (
            <UserInformation user={user} />
          )}
        </section>
      </div>
    </main>
  );
}

function UserInformation({ user }: { user: NonNullable<ReturnType<typeof useUser>["data"]> }) {
  const details = [
    [<Mail size={17} />, "Email", user.email],
    [<Phone size={17} />, "Telefon", user.phone || "—"],
    [<Building2 size={17} />, "Filial", user.branch_name || "—"],
    [<Calendar size={17} />, "Oxirgi kirish", user.last_login ? formatDateTime(user.last_login) : "—"],
    [<Calendar size={17} />, "Ro'yxatdan o'tgan sana", formatDateTime(user.created_at)],
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
