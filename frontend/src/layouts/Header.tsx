import { useEffect, useRef, useState } from "react";
import { Bell, ChevronDown, KeyRound, LogOut, UserRound } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";
import { ASOSIY, matchNavHref } from "./navItems";
import { canAccessPath } from "../lib/permissions";
import { useAuthStore } from "../stores/authStore";
import { roleLabel } from "../pages/users/usersUtils";

// ── Types ──────────────────────────────────────────────────────────────────────

interface HeaderProps {
  pageTitle?: string;
  pageSubtitle?: string;
  notificationCount?: number;
  onNotificationClick?: () => void;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function getUzbekDate(): string {
  const now = new Date();

  const uzMonths = [
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
  const uzDays = [
    "Yakshanba",
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba",
  ];

  const day = now.getDate();
  const month = uzMonths[now.getMonth()];
  const year = now.getFullYear();
  const dayName = uzDays[now.getDay()];

  return `Bugungi sana: ${day}-${month}, ${year} • ${dayName}`;
}

/** Sidebar'da ko'rinmaydigan, lekin sarlavhaga muhtoj sahifalar. */
const EXTRA_TITLES: Record<string, string> = {
  "/profile": "Profil",
};

/** Sarlavha ham URL'dan olinadi, shunda sahifa yangilanganda saqlanib qoladi. */
function getPageTitle(
  pathname: string,
  user: Parameters<typeof canAccessPath>[0],
): string {
  const href = matchNavHref(pathname);
  // Roli yetmagan bo'limda sahifa o'rniga "Ruxsat yo'q" chiqadi — sarlavha ham
  // shunga mos bo'lishi kerak, aks holda yopiq bo'lim nomi ko'rinib qoladi.
  if (href && !canAccessPath(user, href)) return "Ruxsat yo'q";

  return (
    ASOSIY.find((item) => item.href === href)?.label ??
    EXTRA_TITLES[pathname] ??
    "Sahifa topilmadi"
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function PageInfo({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="flex flex-col justify-center">
      <h1 className="text-gray-900 font-bold text-xl leading-tight">{title}</h1>
      <p className="text-gray-400 text-sm mt-0.5">{subtitle}</p>
    </div>
  );
}

function NotificationBell({
  count,
  onClick,
}: {
  count: number;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-white border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all duration-150 shadow-sm"
      aria-label={`${count} ta bildirishnoma`}
    >
      <Bell size={18} className="text-gray-600" />
      {count > 0 && (
        <span
          className="absolute -top-1 -right-1 flex items-center justify-center rounded-full text-white font-bold"
          style={{
            minWidth: 18,
            height: 18,
            fontSize: 10,
            background: "#ef4444",
            padding: "0 4px",
            lineHeight: 1,
          }}
        >
          {count > 99 ? "99+" : count}
        </span>
      )}
    </button>
  );
}

function MenuItem({
  icon,
  label,
  badge,
  danger,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  badge?: number;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      role="menuitem"
      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium text-left transition-colors cursor-pointer ${
        danger
          ? "text-red-600 hover:bg-red-50"
          : "text-gray-700 hover:bg-gray-50"
      }`}
    >
      <span className={danger ? "text-red-500" : "text-gray-400"}>{icon}</span>
      <span className="flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span
          className="flex-shrink-0 rounded-full text-white font-bold text-[10px] px-1.5 py-0.5 min-w-[18px] text-center"
          style={{ background: "#ef4444" }}
        >
          {badge > 99 ? "99+" : badge}
        </span>
      )}
    </button>
  );
}

function UserMenu({ unreadCount }: { unreadCount: number }) {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const userName = user?.full_name?.trim() || user?.email || "Foydalanuvchi";
  // Bir nechta rolli foydalanuvchida hammasini ko'rsatamiz — kim qaysi vakolat
  // bilan ishlayotgani sarlavhadan ko'rinib tursin.
  const userRole = (user?.roles ?? []).map(roleLabel).join(", ") || "—";
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  // Menyu ochiq turganda tashqariga bosish yoki Escape uni yopadi.
  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const go = (to: string) => () => {
    setOpen(false);
    navigate(to);
  };

  const handleLogout = () => {
    setOpen(false);
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="relative" ref={rootRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={`flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl bg-white border transition-all duration-150 shadow-sm cursor-pointer ${
          open
            ? "border-gray-200 bg-gray-50"
            : "border-gray-100 hover:border-gray-200 hover:bg-gray-50"
        }`}
      >
        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
          style={{
            background: "linear-gradient(135deg, #16a34a 0%, #15803d 100%)",
          }}
        >
          {initials}
        </div>

        {/* Name + role */}
        <div className="flex flex-col items-start leading-tight">
          <span className="text-gray-800 text-sm font-semibold whitespace-nowrap">
            {userName}
          </span>
          <span className="text-gray-400 text-xs whitespace-nowrap">
            {userRole}
          </span>
        </div>

        <ChevronDown
          size={14}
          className={`text-gray-400 flex-shrink-0 ml-0.5 transition-transform duration-150 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full mt-2 w-60 rounded-xl bg-white border border-gray-100 p-1.5 z-50"
          style={{ boxShadow: "0 8px 28px rgba(0,0,0,0.12)" }}
        >
          {/* Kim tizimga kirgani — menyu tepasida to'liq ko'rinadi. */}
          <div className="px-3 py-2 border-b border-gray-100 mb-1.5">
            <p className="text-sm font-semibold text-gray-800 truncate">
              {userName}
            </p>
            <p className="text-xs text-gray-400 truncate">
              {user?.email || "—"}
            </p>
            <p className="text-xs text-green-600 font-medium mt-0.5 truncate">
              {userRole}
            </p>
          </div>

          <MenuItem
            icon={<UserRound size={15} />}
            label="Mening ma'lumotlarim"
            onClick={go("/profile")}
          />

          <MenuItem
            icon={<KeyRound size={15} />}
            label="Parolni o'zgartirish"
            onClick={go("/profile#parol")}
          />

          <div className="border-t border-gray-100 my-1.5" />

          <MenuItem
            icon={<LogOut size={15} />}
            label="Chiqish"
            danger
            onClick={handleLogout}
          />
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function Header({
  pageTitle,
  pageSubtitle,
  notificationCount,
  onNotificationClick,
}: HeaderProps) {
  const { pathname } = useLocation();
  const currentUser = useAuthStore((state) => state.user);
  const title = pageTitle ?? getPageTitle(pathname, currentUser);
  const subtitle = pageSubtitle ?? getUzbekDate();
  const navigate = useNavigate();
  const { data: notifications } = useNotifications();
  const unreadCount = (notifications ?? []).filter((n) => !n.is_read).length;

  return (
    <header
      className="flex items-center justify-between px-7 bg-white rounded-t-2xl"
      style={{
        height: 64,
        borderBottom: "1px solid #f0f0f0",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {/* ── Left: page title + date ── */}
      <PageInfo title={title} subtitle={subtitle} />

      {/* ── Right: actions ── */}
      <div className="flex items-center gap-3">
        {/* Bell */}
        <NotificationBell
          count={notificationCount ?? unreadCount}
          onClick={onNotificationClick ?? (() => navigate("/notifications"))}
        />

        {/* User / Role menu */}
        <UserMenu unreadCount={unreadCount} />
      </div>
    </header>
  );
}
