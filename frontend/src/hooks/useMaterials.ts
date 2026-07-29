import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createMaterial, deleteMaterial, getMaterial, getMaterials, materialQueryKey, materialsQueryKey, updateMaterial } from "../api/materials";

export function useMaterials() {
  return useQuery({
    queryKey: materialsQueryKey,
    queryFn: getMaterials,
    select: (response) => response.results,
  });
}

export function useCreateMaterial() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMaterial,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: materialsQueryKey }),
  });
}

export function useMaterial(materialId: number) {
  return useQuery({ queryKey: materialQueryKey(materialId), queryFn: () => getMaterial(materialId), enabled: Number.isInteger(materialId) && materialId > 0 });
}

export function useUpdateMaterial() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: updateMaterial, onSuccess: (material) => { queryClient.setQueryData(materialQueryKey(material.id), material); return queryClient.invalidateQueries({ queryKey: materialsQueryKey }); } });
}

export function useDeleteMaterial() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: deleteMaterial, onSuccess: (_, materialId) => { queryClient.removeQueries({ queryKey: materialQueryKey(materialId) }); return queryClient.invalidateQueries({ queryKey: materialsQueryKey }); } });
}
