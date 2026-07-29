import api from "../lib/axios";
import type { DashboardStats } from "../types/dashboard";

export const dashboardQueryKey = ["dashboard"] as const;

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/dashboard/");
  return data;
}
