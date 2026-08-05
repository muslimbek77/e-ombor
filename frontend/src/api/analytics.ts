import api from "../lib/axios";
import type { AnalyticsOverview } from "../types/analytics";

export const analyticsOverviewQueryKey = ["analytics", "overview"] as const;

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const { data } = await api.get<AnalyticsOverview>("/analytics/overview/");
  return data;
}
