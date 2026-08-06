import type { UserRole } from "../../types/user";

export const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "admin", label: "Tizim administratori" },
  { value: "ceo", label: "Boshqaruv raisi" },
  { value: "architecture", label: "Arxitektura va qurilishni rejalashtirish" },
  { value: "procurement", label: "Xaridlar boshqarmasi" },
  { value: "accountant", label: "Buxgalter" },
  { value: "warehouse", label: "Omborchi" },
  { value: "prorab", label: "Prorab" },
  { value: "branch_manager", label: "Filial rahbari" },
  { value: "anticorruption", label: "Korrupsiyaga qarshi nazorat" },
];

const ROLE_LABELS: Record<string, string> = Object.fromEntries(ROLE_OPTIONS.map((option) => [option.value, option.label]));

export function roleLabel(role: string) {
  return ROLE_LABELS[role] ?? role;
}
