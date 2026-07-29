import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  adjustInventoryItem,
  createInventoryItem,
  getInventory,
  inventoryQueryKey,
} from "../api/inventory";
import { stockMovementsQueryKey } from "../api/stockMovements";
import type { InventoryFilters } from "../api/inventory";

export function useInventory(filters?: InventoryFilters) {
  return useQuery({
    queryKey: filters ? [...inventoryQueryKey, filters] : inventoryQueryKey,
    queryFn: () => getInventory(filters),
    select: (response) => response.results,
  });
}

export function useInventoryItem(itemId: number) {
  return useQuery({
    queryKey: inventoryQueryKey,
    queryFn: () => getInventory(),
    select: (response) => response.results.find((item) => item.id === itemId),
    enabled: Number.isInteger(itemId) && itemId > 0,
  });
}

export function useCreateInventoryItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createInventoryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryQueryKey });
      queryClient.invalidateQueries({ queryKey: stockMovementsQueryKey });
    },
  });
}

export function useAdjustInventoryItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: adjustInventoryItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inventoryQueryKey });
      queryClient.invalidateQueries({ queryKey: stockMovementsQueryKey });
    },
  });
}
