export type TicketCategory = "material_shortage" | "equipment" | "labor" | "other";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";

export interface Ticket {
  id: number;
  title: string;
  description: string;
  category: TicketCategory;
  category_display: string;
  priority: TicketPriority;
  priority_display: string;
  status: TicketStatus;
  status_display: string;
  created_by: number | null;
  created_by_name: string;
  assigned_to: number | null;
  assigned_to_name: string;
  branch: number | null;
  branch_name: string;
  site: number | null;
  site_name: string;
  response: string;
  created_at: string;
  updated_at: string;
}

export interface TicketCreatePayload {
  title: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  site: number | null;
}

export interface TicketUpdatePayload extends TicketCreatePayload {
  status: TicketStatus;
  assigned_to: number | null;
  response: string;
}

export interface TicketsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Ticket[];
}
