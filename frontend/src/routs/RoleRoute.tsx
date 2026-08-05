import { useLocation } from "react-router-dom";
import { matchNavHref } from "../layouts/navItems";
import { canAccessPath } from "../lib/permissions";
import { useAuthStore } from "../stores/authStore";
import ForbiddenPage from "../pages/Forbidden/ForbiddenPage";

/**
 * Manzil bo'yicha rol tekshiruvi. Bo'lim menyuda ko'rinmasa, uni URL orqali
 * qo'lda kiritib ham ochib bo'lmasligi kerak. Detail sahifalar ota bo'lim
 * qoidasiga bo'ysunadi (`/inventory/5` → `/inventory`).
 */
export default function RoleRoute({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const user = useAuthStore((state) => state.user);
  const href = matchNavHref(pathname);

  if (href && !canAccessPath(user, href)) return <ForbiddenPage />;

  return children;
}
