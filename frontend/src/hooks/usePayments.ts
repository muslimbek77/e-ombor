import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createPayment, getPayments, paymentsQueryKey } from "../api/payments";
import { invoiceQueryKey, invoicesQueryKey } from "../api/invoices";

export function usePayments() {
  return useQuery({
    queryKey: paymentsQueryKey,
    queryFn: getPayments,
    select: (response) => response.results,
  });
}

export function useInvoicePayments(invoiceId: number) {
  const { data: payments, ...rest } = usePayments();
  return { ...rest, data: payments?.filter((payment) => payment.invoice === invoiceId) };
}

export function useCreatePayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPayment,
    onSuccess: (payment) => {
      queryClient.invalidateQueries({ queryKey: paymentsQueryKey });
      queryClient.invalidateQueries({ queryKey: invoiceQueryKey(payment.invoice) });
      queryClient.invalidateQueries({ queryKey: invoicesQueryKey });
    },
  });
}
