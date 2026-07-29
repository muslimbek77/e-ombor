import { useQuery } from "@tanstack/react-query";
import { dashboardQueryKey, getDashboardStats } from "../api/dashboard";

export function useDashboard() {
  return useQuery({ queryKey: dashboardQueryKey, queryFn: getDashboardStats });
}
