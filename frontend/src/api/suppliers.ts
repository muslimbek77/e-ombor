import api from "../lib/axios";
import type { Supplier, SupplierPayload, SuppliersResponse } from "../types/supplier";

export const suppliersQueryKey = ["suppliers"] as const;
export const supplierQueryKey = (supplierId: number) => [...suppliersQueryKey, supplierId] as const;

export async function getSuppliers(): Promise<SuppliersResponse> {
  const { data } = await api.get<SuppliersResponse>("/suppliers/");
  return data;
}

export async function createSupplier(payload: SupplierPayload): Promise<Supplier> {
  const { data } = await api.post<Supplier>("/suppliers/", payload);
  return data;
}

export async function getSupplier(supplierId: number): Promise<Supplier> {
  const { data } = await api.get<Supplier>(`/suppliers/${supplierId}/`);
  return data;
}

export async function updateSupplier({ supplierId, payload }: { supplierId: number; payload: SupplierPayload }): Promise<Supplier> {
  const { data } = await api.put<Supplier>(`/suppliers/${supplierId}/`, payload);
  return data;
}

export async function deleteSupplier(supplierId: number): Promise<void> {
  await api.delete(`/suppliers/${supplierId}/`);
}
