import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createWarehouse, deleteWarehouse, getWarehouse, getWarehouses, warehouseQueryKey, warehousesQueryKey, updateWarehouse } from "../api/warehouses";

export function useWarehouses() {
  return useQuery({
    queryKey: warehousesQueryKey,
    queryFn: getWarehouses,
    select: (response) => response.results,
  });
}

export function useCreateWarehouse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createWarehouse,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: warehousesQueryKey }),
  });
}

export function useWarehouse(warehouseId: number) {
  return useQuery({ queryKey: warehouseQueryKey(warehouseId), queryFn: () => getWarehouse(warehouseId), enabled: Number.isInteger(warehouseId) && warehouseId > 0 });
}

export function useUpdateWarehouse() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: updateWarehouse, onSuccess: (warehouse) => { queryClient.setQueryData(warehouseQueryKey(warehouse.id), warehouse); return queryClient.invalidateQueries({ queryKey: warehousesQueryKey }); } });
}

export function useDeleteWarehouse() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: deleteWarehouse, onSuccess: (_, warehouseId) => { queryClient.removeQueries({ queryKey: warehouseQueryKey(warehouseId) }); return queryClient.invalidateQueries({ queryKey: warehousesQueryKey }); } });
}
