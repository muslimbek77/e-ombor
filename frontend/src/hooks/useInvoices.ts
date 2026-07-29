import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createInvoice, getInvoice, getInvoices, invoiceQueryKey, invoicesQueryKey, updateInvoice } from "../api/invoices";

export function useInvoices() {
  return useQuery({
    queryKey: invoicesQueryKey,
    queryFn: getInvoices,
    select: (response) => response.results,
  });
}

export function useInvoice(invoiceId: number) {
  return useQuery({
    queryKey: invoiceQueryKey(invoiceId),
    queryFn: () => getInvoice(invoiceId),
    enabled: Number.isInteger(invoiceId) && invoiceId > 0,
  });
}

export function useCreateInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createInvoice,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: invoicesQueryKey }),
  });
}

export function useUpdateInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateInvoice,
    onSuccess: (invoice) => {
      queryClient.setQueryData(invoiceQueryKey(invoice.id), invoice);
      return queryClient.invalidateQueries({ queryKey: invoicesQueryKey });
    },
  });
}
