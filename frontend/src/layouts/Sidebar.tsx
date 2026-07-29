import { useState } from "react";
import {
  LayoutDashboard,
  Building2,
  ShoppingCart,
  FileText,
  Users,
  Package,
  Boxes,
  Layers,
  Calculator,
  FolderOpen,
  BarChart2,
  MessageSquare,
  Bell,
  UserCog,
  Settings,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";

// ── Types ──────────────────────────────────────────────────────────────────────

interface NavItem {
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

interface SidebarProps {
  activeItem?: string;
  onNavigate?: (href: string) => void;
}

// ── Nav groups ─────────────────────────────────────────────────────────────────

const ASOSIY: NavItem[] = [
  {
    label: "Boshqaruv paneli",
    icon: <LayoutDashboard size={18} />,
    href: "/",
  },
  {
    label: "Qurilish obyektlari",
    icon: <Building2 size={18} />,
    href: "/objects",
  },
  {
    label: "Xaridlar",
    icon: <ShoppingCart size={18} />,
    href: "/purchases",
  },
  {
    label: "Shartnomalar",
    icon: <FileText size={18} />,
    href: "/contracts",
  },
  {
    label: "Supplierlar",
    icon: <Users size={18} />,
    href: "/suppliers",
  },
  {
    label: "Ombor",
    icon: <Package size={18} />,
    href: "/warehouse",
  },
  {
    label: "Inventar",
    icon: <Boxes size={18} />,
    href: "/inventory",
  },
  {
    label: "Materiallar",
    icon: <Layers size={18} />,
    href: "/materials",
  },
  {
    label: "Hisob-fakturalar",
    icon: <Calculator size={18} />,
    href: "/invoices",
  },
  {
    label: "Hujjatlar",
    icon: <FolderOpen size={18} />,
    href: "/documents",
  },
  {
    label: "Hisobotlar",
    icon: <BarChart2 size={18} />,
    href: "/reports",
  },
  {
    label: "Murojaatlar",
    icon: <MessageSquare size={18} />,
    href: "/tickets",
  },
  {
    label: "Bildirishnomalar",
    icon: <Bell size={18} />,
    href: "/notifications",
  },
  {
    label: "Foydalanuvchilar",
    icon: <UserCog size={18} />,
    href: "/users",
  },
  {
    label: "Sozlamalar",
    icon: <Settings size={18} />,
    href: "/settings",
  },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function Logo() {
  return (
    <div className="flex items-center gap-3 px-5 py-5">
      {/* Green cube icon */}
      <div
        className="flex items-center justify-center rounded-lg flex-shrink-0"
        style={{
          width: 40,
          height: 40,
          background: "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)",
        }}
      >
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <path
            d="M11 2L20 7V15L11 20L2 15V7L11 2Z"
            fill="white"
            fillOpacity="0.3"
            stroke="white"
            strokeWidth="1.5"
          />
          <path d="M11 2L20 7L11 12L2 7L11 2Z" fill="white" fillOpacity="0.6" />
          <path d="M11 12V20L2 15V7L11 12Z" fill="white" fillOpacity="0.4" />
          <path d="M11 12V20L20 15V7L11 12Z" fill="white" fillOpacity="0.2" />
        </svg>
      </div>
      <div className="flex flex-col leading-tight">
        <span className="text-white font-bold text-base tracking-wide">
          E-OMBOR
        </span>
        <span className="text-green-400 text-xs font-normal">
          Elektron ombor tizimi
        </span>
      </div>
    </div>
  );
}

function NavLink({
  item,
  isActive,
  onClick,
}: {
  item: NavItem;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      // Replace the className in NavLink button with this:
      className={`
  w-full flex items-center gap-3 px-[13.5px] py-[8.5px] mx-1 rounded-[10px] text-left
  transition-all duration-150 group relative overflow-hidden cursor-pointer
  ${
    isActive
      ? "text-white border border-green-400/35"
      : "text-gray-400/75 border border-transparent hover:text-white/75 hover:bg-white/[0.06] hover:border-white/[0.08]"
  }
`}
      style={
        isActive
          ? {
              background:
                "linear-gradient(135deg, rgba(34,197,94,0.28) 0%, rgba(22,163,74,0.18) 100%)",
              boxShadow:
                "0 4px 16px rgba(34,197,94,0.15), inset 0 1px 0 rgba(255,255,255,0.12)",
              backdropFilter: "blur(8px)",
              WebkitBackdropFilter: "blur(8px)",
              width: "calc(100% - 8px)",
            }
          : { width: "calc(100% - 8px)" }
      }
    >
      {/* Active left accent bar */}
      {isActive && (
        <div
          className="absolute left-[-1px] top-1/2 -translate-y-1/2 w-[3px] h-[18px] rounded-r"
          style={{
            background: "linear-gradient(180deg, #86efac 0%, #22c55e 100%)",
            boxShadow: "0 0 6px rgba(74,222,128,0.6)",
          }}
        />
      )}

      <span
        className={`flex-shrink-0 transition-colors ${
          isActive
            ? "text-green-300"
            : "text-gray-500 group-hover:text-green-400"
        }`}
      >
        {item.icon}
      </span>

      <span className="flex-1 text-sm font-medium truncate">{item.label}</span>

      {item.badge !== undefined && (
        <span
          style={{
            background: isActive ? "rgba(255,255,255,0.22)" : "#16a34a",
            color: "white",
            fontSize: 11,
          }}
          className="flex-shrink-0 text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[20px] text-center"
        >
          {item.badge}
        </span>
      )}
    </button>
  );
}

function SystemStatus() {
  return (
    <div className="mx-4 mb-4">
      <div className="flex items-center gap-2">
        {/* Pulsing green dot */}
        <div className="relative flex-shrink-0">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <div className="absolute inset-0 w-2 h-2 rounded-full bg-green-400 animate-ping opacity-60" />
        </div>
        <div>
          <div className="text-white text-xs font-semibold">Tizim holati</div>
          <div className="text-gray-400 text-xs">
            Barcha tizimlar ishlayapti
          </div>
        </div>
      </div>
    </div>
  );
}

function FooterCopyright() {
  return (
    <div className="px-4 pb-4">
      <p className="text-gray-600 text-xs text-center">
        © 2026 Ko'prikQurilish AJ
      </p>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function Sidebar({ activeItem = "/" }: SidebarProps) {
  const [active, setActive] = useState(activeItem);
  const navigate = useNavigate();
  const { data: notifications } = useNotifications();
  const unreadCount = (notifications ?? []).filter((n) => !n.is_read).length;
  const handleClick = (href: string) => {
    setActive(href);
    navigate(href);
  };

  return (
    <aside
      className="flex flex-col overflow-hidden select-none"
      style={{
        width: 220,
        minWidth: 220,
        background: "linear-gradient(180deg, #0f1c14 0%, #111a13 100%)",
        borderRight: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* ── Logo ── */}
      <Logo />

      {/* ── Divider ── */}
      <div
        className="mx-4 mb-4"
        style={{ height: 1, background: "rgba(255,255,255,0.07)" }}
      />

      {/* ── Section label ── */}
      <div className="px-5 mb-2">
        <span className="text-gray-600 text-xs font-semibold tracking-widest uppercase">
          Asosiy
        </span>
      </div>

      {/* ── Nav items ── */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-1 pb-2 space-y-0.5 scrollbar-thin">
        {ASOSIY.map((item) => (
          <NavLink
            key={item.href}
            item={item.href === "/notifications" && unreadCount > 0 ? { ...item, badge: unreadCount } : item}
            isActive={active === item.href}
            onClick={() => handleClick(item.href)}
          />
        ))}
      </nav>

      {/* ── Divider ── */}
      <div
        className="mx-4 mt-2 mb-4"
        style={{ height: 1, background: "rgba(255,255,255,0.07)" }}
      />

      {/* ── System status ── */}
      {/* <SystemStatus /> */}

      {/* ── Copyright ── */}
      <FooterCopyright />
    </aside>
  );
}
