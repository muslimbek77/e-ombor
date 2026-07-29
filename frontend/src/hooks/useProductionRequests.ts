import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createProductionRequest,
  getProductionRequest,
  getProductionRequests,
  productionRequestQueryKey,
  productionRequestsQueryKey,
  updateProductionRequest,
  updateProductionRequestStatus,
} from "../api/productionRequests";
import type { ProductionRequest } from "../types/productionRequest";

export function useProductionRequests() {
  return useQuery({
    queryKey: productionRequestsQueryKey,
    queryFn: getProductionRequests,
    select: (response) => response.results,
  });
}

export function useProductionRequest(requestId: number) {
  return useQuery({
    queryKey: productionRequestQueryKey(requestId),
    queryFn: () => getProductionRequest(requestId),
    enabled: Number.isInteger(requestId) && requestId > 0,
  });
}

export function useCreateProductionRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProductionRequest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionRequestsQueryKey }),
  });
}

function syncCaches(queryClient: ReturnType<typeof useQueryClient>) {
  return (request: ProductionRequest) => {
    queryClient.setQueryData(productionRequestQueryKey(request.id), request);
    return queryClient.invalidateQueries({ queryKey: productionRequestsQueryKey });
  };
}

export function useUpdateProductionRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateProductionRequest,
    onSuccess: syncCaches(queryClient),
  });
}

export function useUpdateProductionRequestStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateProductionRequestStatus,
    onSuccess: syncCaches(queryClient),
  });
}
