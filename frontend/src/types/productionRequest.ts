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

/**
 * `status` — faqat `PRODUCTION_REQUEST_STATUS_ROLES`
 * (backend: `roles.py: PRODUCTION_REQUEST_STATUS_ROLES`). Muallif uni
 * yubormaydi, aks holda server 403 qaytaradi.
 */
export interface ProductionRequestUpdatePayload extends ProductionRequestCreatePayload {
  status?: ProductionRequestStatus;
}

export interface ProductionRequestsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProductionRequest[];
}
