import api from "../lib/axios";
import type {
  ProductionRequest,
  ProductionRequestCreatePayload,
  ProductionRequestStatus,
  ProductionRequestUpdatePayload,
  ProductionRequestsResponse,
} from "../types/productionRequest";

export const productionRequestsQueryKey = ["production-requests"] as const;
export const productionRequestQueryKey = (requestId: number) => [...productionRequestsQueryKey, requestId] as const;

export async function getProductionRequests(): Promise<ProductionRequestsResponse> {
  const { data } = await api.get<ProductionRequestsResponse>("/production-requests/");
  return data;
}

export async function getProductionRequest(requestId: number): Promise<ProductionRequest> {
  const { data } = await api.get<ProductionRequest>(`/production-requests/${requestId}/`);
  return data;
}

export async function createProductionRequest(payload: ProductionRequestCreatePayload): Promise<ProductionRequest> {
  const { data } = await api.post<ProductionRequest>("/production-requests/", payload);
  return data;
}

export async function updateProductionRequest({ requestId, payload }: { requestId: number; payload: ProductionRequestUpdatePayload }): Promise<ProductionRequest> {
  const { data } = await api.put<ProductionRequest>(`/production-requests/${requestId}/`, payload);
  return data;
}

export async function updateProductionRequestStatus({ requestId, status }: { requestId: number; status: ProductionRequestStatus }): Promise<ProductionRequest> {
  const { data } = await api.patch<ProductionRequest>(`/production-requests/${requestId}/`, { status });
  return data;
}
