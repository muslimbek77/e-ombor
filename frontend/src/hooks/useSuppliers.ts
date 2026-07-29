import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSupplier,
  deleteSupplier,
  getSupplier,
  getSuppliers,
  supplierQueryKey,
  suppliersQueryKey,
  updateSupplier,
} from "../api/suppliers";

export function useSuppliers() {
  return useQuery({
    queryKey: suppliersQueryKey,
    queryFn: getSuppliers,
    select: (response) => response.results,
  });
}

export function useCreateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSupplier,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: suppliersQueryKey }),
  });
}

export function useSupplier(supplierId: number) {
  return useQuery({
    queryKey: supplierQueryKey(supplierId),
    queryFn: () => getSupplier(supplierId),
    enabled: Number.isInteger(supplierId) && supplierId > 0,
  });
}

export function useUpdateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateSupplier,
    onSuccess: (supplier) => {
      queryClient.setQueryData(supplierQueryKey(supplier.id), supplier);
      return queryClient.invalidateQueries({ queryKey: suppliersQueryKey });
    },
  });
}

export function useDeleteSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSupplier,
    onSuccess: (_, supplierId) => {
      queryClient.removeQueries({ queryKey: supplierQueryKey(supplierId) });
      return queryClient.invalidateQueries({ queryKey: suppliersQueryKey });
    },
  });
}
