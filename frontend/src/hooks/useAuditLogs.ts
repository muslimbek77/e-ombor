import { useQuery } from "@tanstack/react-query";
import { auditLogsQueryKey, getAuditLogs } from "../api/auditLogs";

export function useAuditLogs() {
  return useQuery({
    queryKey: auditLogsQueryKey,
    queryFn: getAuditLogs,
    select: (response) => response.results,
  });
}
