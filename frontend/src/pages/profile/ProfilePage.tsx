import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import {
  User,
  Mail,
  Phone,
  Shield,
  Building2,
  Calendar,
  Clock,
  Hash,
  CheckCircle2,
  XCircle,
  LogOut,
} from "lucide-react";

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const months = [
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentabr",
    "oktabr",
    "noyabr",
    "dekabr",
  ];
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

function formatDateTime(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${formatDate(iso)}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function getInitials(firstName: string, lastName: string): string {
  return `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`.toUpperCase() || "?";
}

// ── Field row ──────────────────────────────────────────────────────────────────

function Field({
  icon,
  label,
  value,
  empty,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string | React.ReactNode;
  empty?: string;
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
        {value ? (
          <span className="text-gray-800 text-sm font-medium">{value}</span>
        ) : (
          <span className="text-gray-300 text-sm italic">
            {empty ?? "Kiritilmagan"}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────────

const ProfilePage = () => {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Foydalanuvchi topilmadi
      </div>
    );
  }

  const initials = getInitials(user.first_name, user.last_name);
  const displayName = user.full_name?.trim() || user.first_name || user.email;

  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto space-y-5">
        {/* ── Hero card ── */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
        >
          {/* Green banner */}
          <div
            className="h-28 block relative"
            style={{
              background:
                "linear-gradient(135deg, #0f1c14 0%, #16a34a 60%, #22c55e 100%)",
            }}
          >
            {/* Subtle grid texture */}
            <div
              className="absolute inset-0 opacity-15"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(0deg,transparent,transparent 24px,rgba(255,255,255,0.3) 24px,rgba(255,255,255,0.3) 25px),repeating-linear-gradient(90deg,transparent,transparent 24px,rgba(255,255,255,0.3) 24px,rgba(255,255,255,0.3) 25px)",
              }}
            />
          </div>

          {/* Avatar + name */}
          <div className="bg-white px-6 pb-5 py-5 relative">
            <div className="flex items-end justify-between gap-4 -mt-8 mb-4">
              <div className="flex items-end gap-4 min-w-0">
                {/* Avatar */}
                <div
                  className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold flex-shrink-0 border-4 border-white"
                  style={{
                    background:
                      "linear-gradient(135deg, #16a34a 0%, #0f1c14 100%)",
                    boxShadow: "0 2px 12px rgba(22,163,74,0.3)",
                  }}
                >
                  {initials}
                </div>

                <div className="pb-1 min-w-0">
                  <h2 className="text-gray-900 text-xl font-bold leading-tight truncate">
                    {displayName}
                  </h2>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    {user.is_staff && (
                      <span
                        className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: "#fef9c3", color: "#854d0e" }}
                      >
                        <Shield size={11} /> Admin
                      </span>
                    )}
                    <span
                      className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
                      style={
                        user.is_active
                          ? { background: "#dcfce7", color: "#15803d" }
                          : { background: "#fee2e2", color: "#b91c1c" }
                      }
                    >
                      {user.is_active ? (
                        <>
                          <CheckCircle2 size={11} /> Faol
                        </>
                      ) : (
                        <>
                          <XCircle size={11} /> Nofaol
                        </>
                      )}
                    </span>
                    {user.roles?.length > 0 && (
                      <span
                        className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: "#eff6ff", color: "#1d4ed8" }}
                      >
                        {user.roles.join(", ")}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Logout button */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl transition-colors flex-shrink-0 mb-1 cursor-pointer"
                style={{ background: "#fef2f2", color: "#dc2626" }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#fee2e2";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "#fef2f2";
                }}
              >
                <LogOut size={14} />
                Chiqish
              </button>
            </div>
          </div>
        </div>

        {/* ── Info cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Contact info */}
          <div
            className="bg-white rounded-2xl px-5 py-4"
            style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
          >
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
              Aloqa
            </p>
            <Field icon={<Mail size={15} />} label="Email" value={user.email} />
            <Field
              icon={<Phone size={15} />}
              label="Telefon"
              value={user.phone || undefined}
            />
            <Field
              icon={<User size={15} />}
              label="Ism"
              value={user.first_name || undefined}
            />
            <Field
              icon={<User size={15} />}
              label="Familiya"
              value={user.last_name || undefined}
            />
          </div>

          {/* System info */}
          <div
            className="bg-white rounded-2xl px-5 py-4"
            style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
          >
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
              Tizim
            </p>
            <Field
              icon={<Building2 size={15} />}
              label="Filial"
              value={user.branch ?? undefined}
              empty="Biriktirilmagan"
            />
            <Field
              icon={<Hash size={15} />}
              label="STIR / INN"
              value={user.stir_inn || undefined}
            />
            <Field
              icon={<Calendar size={15} />}
              label="Ro'yxatdan o'tgan"
              value={formatDate(user.created_at)}
            />
            <Field
              icon={<Clock size={15} />}
              label="Oxirgi kirish"
              value={formatDateTime(user.last_login)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
