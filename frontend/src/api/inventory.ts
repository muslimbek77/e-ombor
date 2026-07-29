import api from "../lib/axios";
import type {
  InventoryAdjustmentPayload,
  InventoryItem,
  InventoryItemPayload,
  InventoryResponse,
} from "../types/inventory";

export const inventoryQueryKey = ["inventory"] as const;
export const inventoryItemQueryKey = (itemId: number) => [...inventoryQueryKey, itemId] as const;

export interface InventoryFilters {
  warehouse?: number;
  material?: number;
}

export async function getInventory(filters?: InventoryFilters): Promise<InventoryResponse> {
  const { data } = await api.get<InventoryResponse>("/inventory/", { params: filters });
  return data;
}

export async function createInventoryItem(payload: InventoryItemPayload): Promise<InventoryItem> {
  const { data } = await api.post<InventoryItem>("/inventory/", payload);
  return data;
}

export async function adjustInventoryItem({
  itemId,
  payload,
}: {
  itemId: number;
  payload: InventoryAdjustmentPayload;
}): Promise<InventoryItem> {
  const { data } = await api.patch<InventoryItem>(`/inventory/${itemId}/`, payload);
  return data;
}
