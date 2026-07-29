import api from "../lib/axios";
import type { Material, MaterialPayload, MaterialsResponse } from "../types/material";

export const materialsQueryKey = ["materials"] as const;
export const materialQueryKey = (materialId: number) => [...materialsQueryKey, materialId] as const;

export async function getMaterials(): Promise<MaterialsResponse> {
  const { data } = await api.get<MaterialsResponse>("/materials/");
  return data;
}

export async function createMaterial(payload: MaterialPayload): Promise<Material> {
  const { data } = await api.post<Material>("/materials/", payload);
  return data;
}

export async function getMaterial(materialId: number): Promise<Material> {
  const { data } = await api.get<Material>(`/materials/${materialId}/`);
  return data;
}

export async function updateMaterial({ materialId, payload }: { materialId: number; payload: MaterialPayload }): Promise<Material> {
  const { data } = await api.put<Material>(`/materials/${materialId}/`, payload);
  return data;
}

export async function deleteMaterial(materialId: number): Promise<void> {
  await api.delete(`/materials/${materialId}/`);
}
