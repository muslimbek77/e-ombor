import api from "../lib/axios";
import type { PurchaseOrder, PurchaseOrderCreatePayload, PurchaseOrderUpdatePayload, PurchaseOrdersResponse } from "../types/purchaseOrder";

export const purchaseOrdersQueryKey = ["purchaseOrders"] as const;
export const purchaseOrderQueryKey = (purchaseOrderId: number) => [...purchaseOrdersQueryKey, purchaseOrderId] as const;

export async function getPurchaseOrders(): Promise<PurchaseOrdersResponse> {
  const { data } = await api.get<PurchaseOrdersResponse>("/purchase-orders/");
  return data;
}

export async function createPurchaseOrder(payload: PurchaseOrderCreatePayload): Promise<PurchaseOrder> {
  const { data } = await api.post<PurchaseOrder>("/purchase-orders/", payload);
  return data;
}

export async function getPurchaseOrder(purchaseOrderId: number): Promise<PurchaseOrder> {
  const { data } = await api.get<PurchaseOrder>(`/purchase-orders/${purchaseOrderId}/`);
  return data;
}

export async function updatePurchaseOrder({ purchaseOrderId, payload }: { purchaseOrderId: number; payload: PurchaseOrderUpdatePayload }): Promise<PurchaseOrder> {
  const { data } = await api.put<PurchaseOrder>(`/purchase-orders/${purchaseOrderId}/`, payload);
  return data;
}

export async function deletePurchaseOrder(purchaseOrderId: number): Promise<void> {
  await api.delete(`/purchase-orders/${purchaseOrderId}/`);
}
