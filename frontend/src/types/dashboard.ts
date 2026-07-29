export interface DashboardRecentDocument {
  id: number;
  doc_number: string;
  title: string;
  status: string;
  status_display: string;
  created_at: string;
}

export interface DashboardRecentTicket {
  id: number;
  title: string;
  priority: string;
  priority_display: string;
  status: string;
  status_display: string;
  created_at: string;
}

export interface DashboardNotification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  notification_type: string;
  created_at: string;
}

export interface DashboardStatusBreakdownEntry {
  status: string;
  total: number;
}

export interface DashboardStats {
  total_documents: number;
  pending_approvals: number;
  total_materials: number;
  total_warehouses: number;
  total_sites: number;
  low_stock_items: number;
  recent_documents: DashboardRecentDocument[];
  recent_tickets: DashboardRecentTicket[];
  notifications: DashboardNotification[];
  document_status_breakdown: DashboardStatusBreakdownEntry[];
  payment_summary: {
    total_invoiced: string;
    total_paid: string;
    remaining: string;
  };
  site_budget_summary: {
    total_budget: string;
  };
}
