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
  ClipboardList,
  MessageSquare,
  Bell,
  UserCog,
  Settings,
  History,
  MapPin,
} from "lucide-react";
import { canAccessPath } from "../lib/permissions";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface NavItem {
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

// ── Nav groups ─────────────────────────────────────────────────────────────────

export const ASOSIY: NavItem[] = [
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
    label: "Manzillar",
    icon: <MapPin size={18} />,
    href: "/addresses",
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
    label: "Zayavkalar",
    icon: <ClipboardList size={18} />,
    href: "/production-requests",
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
    label: "Audit jurnali",
    icon: <History size={18} />,
    href: "/audit-logs",
  },
  {
    label: "Sozlamalar",
    icon: <Settings size={18} />,
    href: "/settings",
  },
];

/**
 * Foydalanuvchi rollariga ko'ra ko'rinadigan bo'limlar.
 * Ruxsat jadvali `lib/permissions.ts` da — bu yerda faqat filtrlaymiz.
 */
export function visibleNavItems(user: Parameters<typeof canAccessPath>[0]): NavItem[] {
  return ASOSIY.filter((item) => canAccessPath(user, item.href));
}

/**
 * Joriy manzilga mos keladigan nav item'ning href'ini qaytaradi.
 * Detail sahifalar ham ota bo'limni faol qiladi (`/tickets/5` → `/tickets`).
 * Faol element URL'dan hisoblanadi, state'da saqlanmaydi — aks holda sahifa
 * yangilanganda tanlov yo'qoladi.
 */
export function matchNavHref(pathname: string): string | undefined {
  if (pathname === "/") return "/";

  let best: string | undefined;
  for (const { href } of ASOSIY) {
    if (href === "/") continue;
    if (pathname === href || pathname.startsWith(`${href}/`)) {
      if (!best || href.length > best.length) best = href;
    }
  }

  return best;
}
