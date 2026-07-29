import { useState, useRef } from "react";
import { useLogin } from "../../hooks/auth/useLogin";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

interface FormState {
  email: string;
  password: string;
}

interface FormErrors {
  email: string;
  password: string;
}

export default function LoginPage() {
  const [form, setForm] = useState<FormState>({ email: "", password: "" });
  const [errors, setErrors] = useState<FormErrors>({ email: "", password: "" });
  const [showPass, setShowPass] = useState(false);
  const [success, setSuccess] = useState(false);
  const passwordRef = useRef<HTMLInputElement>(null);

  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const validate = (): boolean => {
    const newErrors: FormErrors = { email: "", password: "" };
    let valid = true;
    const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!form.email.trim()) {
      newErrors.email = "Elektron pochta kiritilmagan";
      valid = false;
    } else if (!emailReg.test(form.email)) {
      newErrors.email = "Noto'g'ri email format";
      valid = false;
    }

    if (!form.password) {
      newErrors.password = "Parol kiritilmagan";
      valid = false;
    } else if (form.password.length < 6) {
      newErrors.password = "Parol kamida 6 ta belgi bo'lishi kerak";
      valid = false;
    }

    setErrors(newErrors);
    return valid;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
  };

  const loginMutation = useLogin();
  const handleLogin = () => {
    if (!validate()) return;

    loginMutation.mutate(form, {
      onSuccess(data) {
        setSuccess(true);
        login(data.access, data.refresh, data.user);
        navigate("/");
      },

      onError(error) {
        console.log(error);
      },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 px-4 relative overflow-hidden">
      {/* Background blobs */}
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-indigo-100/40 blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-[350px] h-[350px] rounded-full bg-purple-100/30 blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-[420px] bg-white/90 backdrop-blur border border-indigo-100 rounded-2xl shadow-xl shadow-indigo-100/30 p-10">
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

        <h1 className="text-xl font-semibold text-indigo-950 mb-1">Kirish</h1>
        <p className="text-[13.5px] text-indigo-400 mb-6">
          Hisobingizga kirish uchun ma'lumotlarni kiriting
        </p>

        {/* Success banner */}
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
            Muvaffaqiyatli kirildi! Yo'naltirilmoqda...
          </div>
        )}

        {/* Email field */}
        <div className="mb-4">
          <label
            htmlFor="email"
            className="flex items-center gap-1.5 text-[13px] font-medium text-indigo-700 mb-1.5"
          >
            <svg
              className="w-3.5 h-3.5 text-indigo-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            Elektron pochta
          </label>
          <div className="relative">
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={handleChange}
              onKeyDown={(e) =>
                e.key === "Enter" && passwordRef.current?.focus()
              }
              placeholder="misol@email.com"
              className={`w-full h-[42px] pl-3.5 pr-10 rounded-xl text-[14px] text-indigo-950 placeholder-indigo-200 bg-indigo-50/50 outline-none transition-all border ${
                errors.email
                  ? "border-red-300 bg-red-50 focus:ring-2 focus:ring-red-100"
                  : "border-indigo-100 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 focus:bg-white"
              }`}
            />
            <svg
              className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          {errors.email && (
            <p className="mt-1 text-[12px] text-red-500 flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              {errors.email}
            </p>
          )}
        </div>

        {/* Password field */}
        <div className="mb-3">
          <label
            htmlFor="password"
            className="flex items-center gap-1.5 text-[13px] font-medium text-indigo-700 mb-1.5"
          >
            <svg
              className="w-3.5 h-3.5 text-indigo-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            Parol
          </label>
          <div className="relative">
            <input
              id="password"
              name="password"
              ref={passwordRef}
              type={showPass ? "text" : "password"}
              autoComplete="current-password"
              value={form.password}
              onChange={handleChange}
              onKeyDown={(e) => e.key === "Enter" && loginMutation.mutate(form)}
              placeholder="Parolni kiriting"
              className={`w-full h-[42px] pl-3.5 pr-10 rounded-xl text-[14px] text-indigo-950 placeholder-indigo-200 bg-indigo-50/50 outline-none transition-all border ${
                errors.password
                  ? "border-red-300 bg-red-50 focus:ring-2 focus:ring-red-100"
                  : "border-indigo-100 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 focus:bg-white"
              }`}
            />
            <button
              type="button"
              onClick={() => setShowPass((p) => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-indigo-300 hover:text-indigo-500 transition-colors"
              aria-label="Parolni ko'rsat/yashir"
            >
              {showPass ? (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                  />
                </svg>
              ) : (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              )}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-[12px] text-red-500 flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              {errors.password}
            </p>
          )}
        </div>

        {/* Forgot password */}
        <div className="flex justify-end mb-5">
          <a
            href="#"
            className="text-[12.5px] text-indigo-500 hover:text-indigo-700 font-medium hover:underline transition-colors"
          >
            Parolni unutdingizmi?
          </a>
        </div>

        {/* Submit button */}
        <button
          onClick={handleLogin}
          disabled={loginMutation.isPending}
          className="w-full h-11 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 active:scale-[0.98] disabled:opacity-70 text-white rounded-xl text-[15px] font-medium flex items-center justify-center gap-2 transition-all cursor-pointer"
        >
          {loginMutation.isPending ? (
            <>
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                />
              </svg>
              Tekshirilmoqda...
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                />
              </svg>
              Kirish
            </>
          )}
        </button>

        <p className="mt-5 flex items-center gap-1 justify-center text-center text-[12px] text-indigo-300">
          Hisob yo'qmi?
          <a
            href="/register"
            className="text-indigo-500 font-medium hover:underline"
          >
            Ro'yxatdan o'ting
          </a>
        </p>
      </div>
    </div>
  );
}
