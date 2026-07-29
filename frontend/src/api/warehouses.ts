import api from "../lib/axios";
import type { Warehouse, WarehousePayload, WarehousesResponse } from "../types/warehouse";

export const warehousesQueryKey = ["warehouses"] as const;
export const warehouseQueryKey = (warehouseId: number) => [...warehousesQueryKey, warehouseId] as const;

export async function getWarehouses(): Promise<WarehousesResponse> {
  const { data } = await api.get<WarehousesResponse>("/warehouses/");
  return data;
}

export async function createWarehouse(payload: WarehousePayload): Promise<Warehouse> {
  const { data } = await api.post<Warehouse>("/warehouses/", payload);
  return data;
}

export async function getWarehouse(warehouseId: number): Promise<Warehouse> {
  const { data } = await api.get<Warehouse>(`/warehouses/${warehouseId}/`);
  return data;
}

export async function updateWarehouse({ warehouseId, payload }: { warehouseId: number; payload: WarehousePayload }): Promise<Warehouse> {
  const { data } = await api.put<Warehouse>(`/warehouses/${warehouseId}/`, payload);
  return data;
}

export async function deleteWarehouse(warehouseId: number): Promise<void> {
  await api.delete(`/warehouses/${warehouseId}/`);
}
