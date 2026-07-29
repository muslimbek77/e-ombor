import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createStockMovement,
  getStockMovements,
  stockMovementsQueryKey,
} from "../api/stockMovements";
import { inventoryQueryKey } from "../api/inventory";
import type { StockMovementFilters } from "../api/stockMovements";

export function useStockMovements(filters?: StockMovementFilters) {
  return useQuery({
    queryKey: filters ? [...stockMovementsQueryKey, filters] : stockMovementsQueryKey,
    queryFn: () => getStockMovements(filters),
    select: (response) => response.results,
  });
}

export function useCreateStockMovement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createStockMovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stockMovementsQueryKey });
      queryClient.invalidateQueries({ queryKey: inventoryQueryKey });
    },
  });
}
