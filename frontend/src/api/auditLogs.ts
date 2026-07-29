import api from "../lib/axios";
import type { AuditLogsResponse } from "../types/auditLog";

export const auditLogsQueryKey = ["audit-logs"] as const;

export async function getAuditLogs(): Promise<AuditLogsResponse> {
  const { data } = await api.get<AuditLogsResponse>("/audit-logs/");
  return data;
}
