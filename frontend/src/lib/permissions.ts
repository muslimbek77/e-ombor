import { useAuthStore } from "../stores/authStore";
import type { UserRole } from "../types/user";

/**
 * Frontend rol tekshiruvi — backenddagi `api/roles.py` qoidalarining nusxasi.
 * Bu yerdagi hech narsa xavfsizlik chorasi emas: server baribir har bir so'rovni
 * qaytadan tekshiradi. Maqsad — foydalanuvchiga bosgandan keyin 403 olmaydigan
 * tugmalarni va kira olmaydigan bo'limlarni umuman ko'rsatmaslik.
 */

// ── Backenddagi rol to'plamlari (roles.py: ADMIN_ROLES, ARCHIVE_ROLES, ...) ────

export const ADMIN_ROLES: UserRole[] = ["admin"];
/**
 * Tashkilot bo'ylab ko'radigan rollar. Bu faqat KO'RISH doirasi — yozish
 * huquqi quyidagi to'plamlar bilan aniqlanadi va bunga bog'liq emas.
 *
 * `architecture` va `accountant` zanjir bosqichi bo'lgani uchun shu yerda:
 * o'z navbatidagi hujjatni ko'ra olmasa zanjir to'xtab qolardi. `warehouse`
 * esa yo'q — u tovarni jismonan qabul qiladi, ya'ni filialga bog'langan.
 */
export const GLOBAL_SCOPE_ROLES: UserRole[] = ["admin", "ceo", "procurement", "anticorruption", "architecture", "accountant"];
export const ARCHIVE_ROLES: UserRole[] = ["admin", "procurement", "branch_manager"];
export const STOCK_MOVEMENT_ROLES: UserRole[] = ["admin", "warehouse"];
/** Filial rahbari so'rovning material qatorlarini o'zi to'ldiradi. */
export const PURCHASE_ORDER_ROLES: UserRole[] = ["admin", "procurement", "branch_manager"];
export const CONTRACT_ROLES: UserRole[] = ["admin", "procurement"];
export const SUPPLIER_ROLES: UserRole[] = ["admin", "procurement"];
export const INVOICE_ROLES: UserRole[] = ["admin", "accountant", "procurement"];
export const PAYMENT_ROLES: UserRole[] = ["admin", "accountant"];
export const SITE_ROLES: UserRole[] = ["admin", "branch_manager", "architecture"];
/**
 * Xaridlar bo'limi bu yerda ataylab yo'q: u begona hujjatni o'zi tahrirlamaydi
 * va o'chirmaydi — filial rahbariga aytadi, tuzatishni u kiritadi.
 */
export const DOCUMENT_MANAGE_ROLES: UserRole[] = ["admin", "branch_manager"];

/**
 * Nazorat roli. Serverda (`api/permissions.py: ControlRoleReadOnly`) unga
 * SAFE_METHODS dan boshqa hamma narsa yopiq — yagona ish-mazmunli istisno
 * `documents/<id>/workflow/`. Bu yerda uni bilishimiz kerak, aks holda
 * bosilganda 403 beradigan tugmalarni ko'rsatib qo'yardik.
 */
export const CONTROL_ROLE: UserRole = "anticorruption";

/**
 * Ma'lumotnoma bazasi — filial, material, ombor, manzil. Ko'rish hammaga
 * ochiq, o'zgartirish faqat adminga (permissions.py: AdminOnlyWrite).
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
  "/purchases": ["ceo", "procurement", "accountant", "branch_manager", "anticorruption"],
  "/contracts": ["ceo", "procurement", "accountant", "branch_manager", "anticorruption"],
  "/suppliers": ["procurement", "accountant", "branch_manager", "anticorruption"],
  "/addresses": ["procurement", "warehouse", "branch_manager"],
  "/warehouse": ["warehouse", "prorab", "procurement", "branch_manager", "anticorruption"],
  "/inventory": ["warehouse", "prorab", "procurement", "branch_manager", "anticorruption"],
  "/materials": ["warehouse", "prorab", "procurement", "branch_manager"],
  "/invoices": ["ceo", "accountant", "procurement", "branch_manager", "anticorruption"],
  "/production-requests": ["prorab", "warehouse", "procurement", "branch_manager"],
  "/reports": ["ceo", "architecture", "accountant", "branch_manager", "anticorruption"],
  "/users": [],
  // Audit log — nazorat rolining asosiy ish quroli.
  "/audit-logs": ["branch_manager", "anticorruption"],
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

/**
 * Nazorat roli — tizimda faqat o'qiydi. `isAdmin` dan farqli o'laroq bu yerda
 * `is_staff` tekshirilmaydi: serverda ham u nazoratga imtiyoz bermaydi, va
 * ikkala rolni bir hisobda birlashtirish umuman taqiqlangan (SoD).
 */
export function isControlRole(user: RoleBearer | null | undefined): boolean {
  return Boolean(user) && (user!.roles ?? []).includes(CONTROL_ROLE);
}

/** Admin hamma narsaga kiradi; qolganlarda rollardan bittasi mos kelishi yetarli. */
export function hasRole(user: RoleBearer | null | undefined, allowed: readonly UserRole[]): boolean {
  if (!user) return false;
  if (isAdmin(user)) return true;
  const roles = user.roles ?? [];
  return allowed.some((role) => roles.includes(role));
}

/**
 * Yozish darvozasi — `hasRole` dan farqi shundaki, nazorat roli bu yerda
 * har doim `false` oladi. Ikkalasi ataylab ajratilgan: nazorat bo'limlarni
 * KO'RADI (`canAccessPath` — hisob-faktura, xarid, audit log uning ish
 * quroli), lekin ularda hech nimani o'zgartira olmaydi.
 */
export function canWrite(user: RoleBearer | null | undefined, allowed: readonly UserRole[]): boolean {
  if (isControlRole(user)) return false;
  return hasRole(user, allowed);
}

export function canAccessPath(user: RoleBearer | null | undefined, href: string): boolean {
  const allowed = PATH_ROLES[href];
  if (!allowed) return true;
  return hasRole(user, allowed);
}

// ── Hook'lar ───────────────────────────────────────────────────────────────────

/**
 * Joriy foydalanuvchi shu bo'limda nimadir o'zgartira oladimi.
 *
 * Chaqiruvchilar buni yozish tugmalarini ko'rsatish uchun ishlatadi, shuning
 * uchun u `canWrite` ga tayanadi va nazorat roliga hech qachon `true`
 * qaytarmaydi. Bo'lim KO'RINISHI uchun `canAccessPath` bor.
 */
export function useHasRole(allowed: readonly UserRole[]): boolean {
  return canWrite(useAuthStore((state) => state.user), allowed);
}

export function useIsAdmin(): boolean {
  return isAdmin(useAuthStore((state) => state.user));
}

/** Joriy foydalanuvchi nazorat rolimi — interfeys unga faqat o'qishni ko'rsatadi. */
export function useIsControlRole(): boolean {
  return isControlRole(useAuthStore((state) => state.user));
}
