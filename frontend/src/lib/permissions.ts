import { useAuthStore } from "../stores/authStore";
import type { UserRole } from "../types/user";

/**
 * Frontend rol tekshiruvi — backenddagi `api/views.py` qoidalarining nusxasi.
 * Bu yerdagi hech narsa xavfsizlik chorasi emas: server baribir har bir so'rovni
 * qaytadan tekshiradi. Maqsad — foydalanuvchiga bosgandan keyin 403 olmaydigan
 * tugmalarni va kira olmaydigan bo'limlarni umuman ko'rsatmaslik.
 */

// ── Backenddagi rol to'plamlari (views.py: ADMIN_ROLES, ARCHIVE_ROLES, ...) ─────

export const ADMIN_ROLES: UserRole[] = ["admin"];
export const ARCHIVE_ROLES: UserRole[] = ["admin", "procurement", "branch_manager"];
export const STOCK_MOVEMENT_ROLES: UserRole[] = ["admin", "warehouse"];
export const PURCHASE_ORDER_ROLES: UserRole[] = ["admin", "procurement"];
export const CONTRACT_ROLES: UserRole[] = ["admin", "procurement"];
export const SUPPLIER_ROLES: UserRole[] = ["admin", "procurement"];
export const INVOICE_ROLES: UserRole[] = ["admin", "accountant", "procurement"];
export const PAYMENT_ROLES: UserRole[] = ["admin", "accountant"];
export const SITE_ROLES: UserRole[] = ["admin", "branch_manager", "architecture"];
export const DOCUMENT_MANAGE_ROLES: UserRole[] = ["admin", "procurement", "branch_manager"];

/**
 * Ma'lumotnoma bazasi — filial, material, ombor, manzil. Ko'rish hammaga
 * ochiq, o'zgartirish faqat adminga (views.py: AdminOnlyWrite).
 */
export const REFERENCE_DATA_ROLES: UserRole[] = ["admin"];

/**
 * Qaysi bo'limni qaysi rol ko'radi. Kalit — nav item'ning `href`i.
 * Ro'yxatda yo'q manzil hamma rolga ochiq (masalan `/`, `/profile`, `/settings`).
 * Admin (yoki `is_staff`) hamma narsani ko'radi — bu alohida tekshiriladi.
 *
 * Bu jadval bo'lim KO'RINISHI haqida — mahsulot qarori, backend cheklovi emas
 * (`/users` va `/audit-logs` bundan istisno, ular serverda ham yopiq).
 * Bo'lim ichida nimani O'ZGARTIRISH mumkinligi esa yuqoridagi rol
 * to'plamlari bilan aniqlanadi va serverda ham xuddi shunday tekshiriladi.
 */
export const PATH_ROLES: Record<string, UserRole[]> = {
  "/purchases": ["ceo", "procurement", "accountant", "branch_manager"],
  "/contracts": ["ceo", "procurement", "accountant", "branch_manager"],
  "/suppliers": ["procurement", "accountant", "branch_manager"],
  "/addresses": ["procurement", "warehouse", "branch_manager"],
  "/warehouse": ["warehouse", "prorab", "procurement", "branch_manager"],
  "/inventory": ["warehouse", "prorab", "procurement", "branch_manager"],
  "/materials": ["warehouse", "prorab", "procurement", "branch_manager"],
  "/invoices": ["ceo", "accountant", "procurement", "branch_manager"],
  "/production-requests": ["prorab", "warehouse", "procurement", "branch_manager"],
  "/reports": ["ceo", "architecture", "accountant", "branch_manager"],
  "/users": [],
  "/audit-logs": ["branch_manager"],
};

// ── Tekshiruvchilar ────────────────────────────────────────────────────────────

interface RoleBearer {
  roles?: string[] | null;
  is_staff?: boolean;
}

export function isAdmin(user: RoleBearer | null | undefined): boolean {
  if (!user) return false;
  return Boolean(user.is_staff) || (user.roles ?? []).includes("admin");
}

/** Admin hamma narsaga kiradi; qolganlarda rollardan bittasi mos kelishi yetarli. */
export function hasRole(user: RoleBearer | null | undefined, allowed: readonly UserRole[]): boolean {
  if (!user) return false;
  if (isAdmin(user)) return true;
  const roles = user.roles ?? [];
  return allowed.some((role) => roles.includes(role));
}

export function canAccessPath(user: RoleBearer | null | undefined, href: string): boolean {
  const allowed = PATH_ROLES[href];
  if (!allowed) return true;
  return hasRole(user, allowed);
}

// ── Hook'lar ───────────────────────────────────────────────────────────────────

/** Joriy foydalanuvchi berilgan rollardan biriga egami. */
export function useHasRole(allowed: readonly UserRole[]): boolean {
  return hasRole(useAuthStore((state) => state.user), allowed);
}

export function useIsAdmin(): boolean {
  return isAdmin(useAuthStore((state) => state.user));
}
