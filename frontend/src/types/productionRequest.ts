export type ProductionRequestStatus = "pending" | "approved" | "delivered" | "cancelled";

export interface ProductionRequest {
  id: number;
  site: number;
  site_name: string;
  request_number: string;
  title: string;
  description: string;
  status: ProductionRequestStatus;
  status_display: string;
  created_by: number | null;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface ProductionRequestCreatePayload {
  site: number;
  title: string;
  description: string;
}

export interface ProductionRequestUpdatePayload extends ProductionRequestCreatePayload {
  status: ProductionRequestStatus;
}

export interface ProductionRequestsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProductionRequest[];
}
