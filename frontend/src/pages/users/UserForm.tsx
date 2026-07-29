import { useState } from "react";
import { useBranches } from "../../hooks/useBranches";
import type { AppUser, UserCreatePayload, UserRole, UserUpdatePayload } from "../../types/user";
import { ROLE_OPTIONS } from "./usersUtils";

const inputClassName = "w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-green-500 focus:ring-2 focus:ring-green-500/20";

interface UserFormValues {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
  stir_inn: string;
  roles: UserRole[];
  branch: string;
  is_active: boolean;
  is_staff: boolean;
}

function getFormValues(user?: AppUser): UserFormValues {
  if (!user) {
    return { email: "", password: "", first_name: "", last_name: "", phone: "", stir_inn: "", roles: [], branch: "", is_active: true, is_staff: false };
  }
  return {
    email: user.email,
    password: "",
    first_name: user.first_name,
    last_name: user.last_name,
    phone: user.phone,
    stir_inn: user.stir_inn,
    roles: user.roles as UserRole[],
    branch: user.branch ? String(user.branch) : "",
    is_active: user.is_active,
    is_staff: user.is_staff,
  };
}

interface UserFormProps {
  initialUser?: AppUser;
  submitLabel?: string;
  isSubmitting?: boolean;
  onSubmit: (payload: UserCreatePayload | UserUpdatePayload) => void;
  onCancel: () => void;
}

export function UserForm({ initialUser, submitLabel = "Yaratish", isSubmitting, onSubmit, onCancel }: UserFormProps) {
  const isEditing = Boolean(initialUser);
  const [values, setValues] = useState<UserFormValues>(() => getFormValues(initialUser));
  const { data: branches = [], isPending: isBranchesPending } = useBranches();

  function updateField<Key extends keyof UserFormValues>(key: Key, value: UserFormValues[Key]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  function toggleRole(role: UserRole) {
    setValues((current) => ({
      ...current,
      roles: current.roles.includes(role) ? current.roles.filter((r) => r !== role) : [...current.roles, role],
    }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const basePayload = {
      email: values.email,
      first_name: values.first_name,
      last_name: values.last_name,
      phone: values.phone,
      stir_inn: values.stir_inn,
      roles: values.roles,
      branch: values.branch ? Number(values.branch) : null,
      is_active: values.is_active,
      is_staff: values.is_staff,
    };

    if (!initialUser) {
      onSubmit({ ...basePayload, password: values.password } satisfies UserCreatePayload);
      return;
    }

    onSubmit({ ...basePayload, ...(values.password ? { password: values.password } : {}) } satisfies UserUpdatePayload);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Ism">
          <input required value={values.first_name} onChange={(event) => updateField("first_name", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Familiya">
          <input required value={values.last_name} onChange={(event) => updateField("last_name", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Email">
          <input required type="email" value={values.email} onChange={(event) => updateField("email", event.target.value)} className={inputClassName} />
        </Field>
        <Field label={isEditing ? "Parol (ixtiyoriy)" : "Parol"}>
          <input required={!isEditing} type="password" value={values.password} onChange={(event) => updateField("password", event.target.value)} placeholder={isEditing ? "O'zgartirmaslik uchun bo'sh qoldiring" : ""} className={inputClassName} />
        </Field>
        <Field label="Telefon">
          <input value={values.phone} onChange={(event) => updateField("phone", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="STIR/INN">
          <input value={values.stir_inn} onChange={(event) => updateField("stir_inn", event.target.value)} className={inputClassName} />
        </Field>
        <Field label="Filial (ixtiyoriy)">
          <select disabled={isBranchesPending} value={values.branch} onChange={(event) => updateField("branch", event.target.value)} className={inputClassName}>
            <option value="">Tanlanmagan</option>
            {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
          </select>
        </Field>
        <Field label="Holati">
          <div className="flex items-center gap-4 pt-2">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={values.is_active} onChange={(event) => updateField("is_active", event.target.checked)} />
              Faol
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={values.is_staff} onChange={(event) => updateField("is_staff", event.target.checked)} />
              Xodim (staff)
            </label>
          </div>
        </Field>
      </div>
      <Field label="Rollar">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {ROLE_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-700">
              <input type="checkbox" checked={values.roles.includes(option.value)} onChange={() => toggleRole(option.value)} />
              {option.label}
            </label>
          ))}
        </div>
      </Field>
      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={onCancel} className="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100">Bekor qilish</button>
        <button disabled={isSubmitting} type="submit" className="rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60">
          {isSubmitting ? "Saqlanmoqda..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function Field({ label, children, className = "" }: { label: string; children: React.ReactNode; className?: string }) {
  return <label className={`block space-y-1.5 text-sm font-medium text-gray-700 ${className}`}><span>{label}</span>{children}</label>;
}
