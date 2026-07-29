import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createPurchaseOrder, deletePurchaseOrder, getPurchaseOrder, getPurchaseOrders, purchaseOrderQueryKey, purchaseOrdersQueryKey, updatePurchaseOrder } from "../api/purchaseOrders";

export function usePurchaseOrders() {
  return useQuery({
    queryKey: purchaseOrdersQueryKey,
    queryFn: getPurchaseOrders,
    select: (response) => response.results,
  });
}

export function useCreatePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPurchaseOrder,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: purchaseOrdersQueryKey }),
  });
}

export function usePurchaseOrder(purchaseOrderId: number) {
  return useQuery({ queryKey: purchaseOrderQueryKey(purchaseOrderId), queryFn: () => getPurchaseOrder(purchaseOrderId), enabled: Number.isInteger(purchaseOrderId) && purchaseOrderId > 0 });
}

export function useUpdatePurchaseOrder() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: updatePurchaseOrder, onSuccess: (purchaseOrder) => { queryClient.setQueryData(purchaseOrderQueryKey(purchaseOrder.id), purchaseOrder); return queryClient.invalidateQueries({ queryKey: purchaseOrdersQueryKey }); } });
}

export function useDeletePurchaseOrder() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: deletePurchaseOrder, onSuccess: (_, purchaseOrderId) => { queryClient.removeQueries({ queryKey: purchaseOrderQueryKey(purchaseOrderId) }); return queryClient.invalidateQueries({ queryKey: purchaseOrdersQueryKey }); } });
}
