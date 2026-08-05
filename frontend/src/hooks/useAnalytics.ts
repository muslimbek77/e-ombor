import { useQuery } from "@tanstack/react-query";
import { analyticsOverviewQueryKey, getAnalyticsOverview } from "../api/analytics";

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: analyticsOverviewQueryKey,
    queryFn: getAnalyticsOverview,
  });
}
