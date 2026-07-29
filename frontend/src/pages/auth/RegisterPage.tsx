import { useState, useRef } from "react";

interface FormState {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone: string;
  stir_inn: string;
  roles: string;
  branch: number;
}

interface FormErrors {
  [key: string]: string;
}

const ROLE_OPTIONS = [
  { value: "admin", label: "Administrator" },
  { value: "manager", label: "Menejer" },
  { value: "warehouse_keeper", label: "Ombor mudiri" },
  { value: "worker", label: "Xodim" },
];
const ErrorText = ({ field, errors }: { field: string, errors: FormErrors }) =>
  errors[field] ? (
    <p className="mt-1 text-[12px] text-red-500 flex items-center gap-1">
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clipRule="evenodd"
        />
      </svg>
      {errors[field]}
    </p>
  ) : null;

export default function RegisterPage() {
  const [form, setForm] = useState<FormState>({
    email: "",
    password: "",
    password_confirm: "",
    first_name: "",
    last_name: "",
    phone: "",
    stir_inn: "",
    roles: "",
    branch: 0,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPass, setShowPass] = useState(false);
  const [showPassConfirm, setShowPassConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const lastNameRef = useRef<HTMLInputElement>(null);
  const phoneRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const stirRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const passwordConfirmRef = useRef<HTMLInputElement>(null);

  const validate = (): boolean => {
    const e: FormErrors = {};
    const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneReg = /^\+?\d{9,13}$/;

    if (!form.first_name.trim()) e.first_name = "Ism kiritilmagan";
    if (!form.last_name.trim()) e.last_name = "Familiya kiritilmagan";

    if (!form.email.trim()) e.email = "Elektron pochta kiritilmagan";
    else if (!emailReg.test(form.email)) e.email = "Noto'g'ri email format";

    if (!form.phone.trim()) e.phone = "Telefon raqam kiritilmagan";
    else if (!phoneReg.test(form.phone.replace(/\s/g, "")))
      e.phone = "Noto'g'ri telefon format";

    if (!form.stir_inn.trim()) e.stir_inn = "STIR kiritilmagan";

    if (!form.roles) e.roles = "Lavozim tanlanmagan";

    if (!form.branch) e.branch = "Filial tanlanmagan";

    if (!form.password) e.password = "Parol kiritilmagan";
    else if (form.password.length < 6)
      e.password = "Parol kamida 6 ta belgi bo'lishi kerak";

    if (!form.password_confirm) e.password_confirm = "Parolni tasdiqlang";
    else if (form.password_confirm !== form.password)
      e.password_confirm = "Parollar mos kelmadi";

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "branch" ? Number(value) : value,
    }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const handleRegister = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      // TODO: replace with real API call
      // await axios.post("/api/auth/register", form);
      await new Promise((res) => setTimeout(res, 1500));
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } finally {
      setLoading(false);
    }
  };

  const inputCls = (field: string) =>
    `w-full h-[42px] pl-3.5 pr-10 rounded-xl text-[14px] text-indigo-950 placeholder-indigo-200 bg-indigo-50/50 outline-none transition-all border ${
      errors[field]
        ? "border-red-300 bg-red-50 focus:ring-2 focus:ring-red-100"
        : "border-indigo-100 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 focus:bg-white"
    }`;

  const labelCls =
    "flex items-center gap-1.5 text-[13px] font-medium text-indigo-700 mb-1.5";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4 py-10 relative overflow-hidden">
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-indigo-100/40 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-[350px] h-[350px] rounded-full bg-purple-100/30 blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-[460px] bg-white/90 backdrop-blur border border-indigo-100 rounded-2xl shadow-xl shadow-indigo-100/30 p-10">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 22 22" fill="none" className="w-5 h-5">
              <rect
                x="2"
                y="5"
                width="18"
                height="14"
                rx="2.5"
                stroke="white"
                strokeWidth="1.5"
              />
              <path
                d="M7 5V4C7 2.9 7.9 2 9 2h4c1.1 0 2 .9 2 2v1"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <path
                d="M6 11h10M6 14.5h6"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <p className="text-lg font-semibold text-indigo-950 leading-tight">
              E-Ombor
            </p>
            <p className="text-[11px] text-indigo-400 tracking-wide">
              Elektron ombor tizimi
            </p>
          </div>
        </div>

        <div className="h-px bg-gradient-to-r from-transparent via-indigo-100 to-transparent mb-6" />

        <h1 className="text-xl font-semibold text-indigo-950 mb-1">
          Ro'yxatdan o'tish
        </h1>
        <p className="text-[13.5px] text-indigo-400 mb-6">
          Tizimdan foydalanish uchun ma'lumotlaringizni kiriting
        </p>

        {success && (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-xl px-4 py-3 mb-5 text-green-700 text-[13.5px]">
            <svg
              className="w-4 h-4 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
            Muvaffaqiyatli ro'yxatdan o'tdingiz!
          </div>
        )}

        {/* Ism / Familiya */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className={labelCls}>Ism</label>
            <input
              name="first_name"
              value={form.first_name}
              onChange={handleChange}
              onKeyDown={(e) =>
                e.key === "Enter" && lastNameRef.current?.focus()
              }
              placeholder="Ism"
              className={inputCls("first_name")}
            />
            <ErrorText errors={errors} field="first_name" />
          </div>
          <div>
            <label className={labelCls}>Familiya</label>
            <input
              name="last_name"
              ref={lastNameRef}
              value={form.last_name}
              onChange={handleChange}
              onKeyDown={(e) => e.key === "Enter" && emailRef.current?.focus()}
              placeholder="Familiya"
              className={inputCls("last_name")}
            />
            <ErrorText errors={errors} field="last_name" />
          </div>
        </div>

        {/* Email */}
        <div className="mb-4">
          <label className={labelCls}>Elektron pochta</label>
          <input
            name="email"
            ref={emailRef}
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={handleChange}
            onKeyDown={(e) => e.key === "Enter" && phoneRef.current?.focus()}
            placeholder="misol@email.com"
            className={inputCls("email")}
          />
          <ErrorText errors={errors} field="email" />
        </div>

        {/* Telefon / STIR */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className={labelCls}>Telefon raqam</label>
            <input
              name="phone"
              ref={phoneRef}
              value={form.phone}
              onChange={handleChange}
              onKeyDown={(e) => e.key === "Enter" && stirRef.current?.focus()}
              placeholder="+998901234567"
              className={inputCls("phone")}
            />
            <ErrorText errors={errors} field="phone" />
          </div>
          <div>
            <label className={labelCls}>STIR (INN)</label>
            <input
              name="stir_inn"
              ref={stirRef}
              value={form.stir_inn}
              onChange={handleChange}
              onKeyDown={(e) =>
                e.key === "Enter" && passwordRef.current?.focus()
              }
              placeholder="123456789"
              className={inputCls("stir_inn")}
            />
            <ErrorText errors={errors} field="stir_inn" />
          </div>
        </div>

        {/* Lavozim / Filial */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className={labelCls}>Lavozim</label>
            <select
              name="roles"
              value={form.roles}
              onChange={handleChange}
              className={inputCls("roles") + " pr-3"}
            >
              <option value="">Tanlang</option>
              {ROLE_OPTIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            <ErrorText errors={errors} field="roles" />
          </div>
          <div>
            <label className={labelCls}>Filial ID</label>
            <input
              name="branch"
              type="number"
              min={0}
              value={form.branch || ""}
              onChange={handleChange}
              placeholder="Filial raqami"
              className={inputCls("branch")}
            />
            <ErrorText errors={errors} field="branch" />
          </div>
        </div>

        {/* Parol */}
        <div className="mb-4">
          <label className={labelCls}>Parol</label>
          <div className="relative">
            <input
              name="password"
              ref={passwordRef}
              type={showPass ? "text" : "password"}
              autoComplete="new-password"
              value={form.password}
              onChange={handleChange}
              onKeyDown={(e) =>
                e.key === "Enter" && passwordConfirmRef.current?.focus()
              }
              placeholder="Parolni kiriting"
              className={inputCls("password")}
            />
            <button
              type="button"
              onClick={() => setShowPass((p) => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-indigo-300 hover:text-indigo-500 transition-colors"
              aria-label="Parolni ko'rsat/yashir"
            >
              {showPass ? "🙈" : "👁"}
            </button>
          </div>
          <ErrorText errors={errors} field="password" />
        </div>

        {/* Parolni tasdiqlash */}
        <div className="mb-5">
          <label className={labelCls}>Parolni tasdiqlang</label>
          <div className="relative">
            <input
              name="password_confirm"
              ref={passwordConfirmRef}
              type={showPassConfirm ? "text" : "password"}
              autoComplete="new-password"
              value={form.password_confirm}
              onChange={handleChange}
              onKeyDown={(e) => e.key === "Enter" && handleRegister()}
              placeholder="Parolni qaytatkiriting"
              className={inputCls("password_confirm")}
            />
            <button
              type="button"
              onClick={() => setShowPassConfirm((p) => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-indigo-300 hover:text-indigo-500 transition-colors"
              aria-label="Parolni ko'rsat/yashir"
            >
              {showPassConfirm ? "🙈" : "👁"}
            </button>
          </div>
          <ErrorText errors={errors} field="password_confirm" />
        </div>

        {/* Submit */}
        <button
          onClick={handleRegister}
          disabled={loading}
          className="w-full h-11 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 active:scale-[0.98] disabled:opacity-70 text-white rounded-xl text-[15px] font-medium flex items-center justify-center gap-2 transition-all"
        >
          {loading ? "Yuborilmoqda..." : "Ro'yxatdan o'tish"}
        </button>

        <p className="mt-5 text-center text-[12px] text-indigo-300">
          Hisobingiz bormi?{" "}
          <a
            href="/login"
            className="text-indigo-500 font-medium hover:underline"
          >
            Kirish
          </a>
        </p>
      </div>
    </div>
  );
}
