import type { InventoryItem } from "./inventory";
import type { Invoice } from "./invoice";
import type { DocStatus, DocType } from "./document";
import type { TicketPriority, TicketStatus } from "./ticket";
import type { AuditLog } from "./auditLog";

export interface DocTypeCount {
  doc_type: DocType;
  total: number;
}

export interface DocStatusCount {
  status: DocStatus;
  total: number;
}

export interface TicketPriorityCount {
  priority: TicketPriority;
  total: number;
}

export interface TicketStatusCount {
  status: TicketStatus;
  total: number;
}

export interface AnalyticsOverview {
  documents_by_type: DocTypeCount[];
  documents_by_status: DocStatusCount[];
  tickets_by_priority: TicketPriorityCount[];
  tickets_by_status: TicketStatusCount[];
  overdue_invoices: Invoice[];
  low_stock_items: InventoryItem[];
  recent_audit_logs: AuditLog[];
}
