import { Bell, Building2, ChevronDown } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";
import { ASOSIY, matchNavHref } from "./navItems";

// ── Types ──────────────────────────────────────────────────────────────────────

interface HeaderProps {
  pageTitle?: string;
  pageSubtitle?: string;
  notificationCount?: number;
  companyName?: string;
  userName?: string;
  userRole?: string;
  onNotificationClick?: () => void;
  onCompanyClick?: () => void;
  onUserMenuClick?: () => void;
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
function getPageTitle(pathname: string): string {
  const href = matchNavHref(pathname);

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

function CompanyBadge({
  name,
  onClick,
}: {
  name: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all duration-150 shadow-sm"
    >
      {/* Company icon */}
      <div
        className="flex items-center justify-center w-6 h-6 rounded-md flex-shrink-0"
        style={{
          background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
        }}
      >
        <Building2 size={13} className="text-white" />
      </div>
      <span className="text-gray-700 text-sm font-semibold whitespace-nowrap">
        {name}
      </span>
    </button>
  );
}

function UserMenu() {
  const navigate = useNavigate();
  const userName = "Jasur Dilmurodov";
  const userRole = "Rais";
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const onClick = () => {
    console.log("User menu clicked");
    navigate("/profile");
  };

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl bg-white border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all duration-150 shadow-sm cursor-pointer"
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

      <ChevronDown size={14} className="text-gray-400 flex-shrink-0 ml-0.5" />
    </button>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function Header({
  pageTitle,
  pageSubtitle,
  notificationCount,
  companyName = "Ko'prikQurilish AJ",
  onNotificationClick,
  onCompanyClick,
}: HeaderProps) {
  const { pathname } = useLocation();
  const title = pageTitle ?? getPageTitle(pathname);
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

        {/* Company */}
        <CompanyBadge name={companyName} onClick={onCompanyClick} />

        {/* User / Role menu */}
        <UserMenu />
      </div>
    </header>
  );
}
