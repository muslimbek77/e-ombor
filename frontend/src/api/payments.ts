import api from "../lib/axios";
import type { Payment, PaymentCreatePayload, PaymentsResponse } from "../types/payment";

export const paymentsQueryKey = ["payments"] as const;

export async function getPayments(): Promise<PaymentsResponse> {
  const { data } = await api.get<PaymentsResponse>("/payments/");
  return data;
}

export async function createPayment({ invoiceId, payload }: { invoiceId: number; payload: PaymentCreatePayload }): Promise<Payment> {
  const { data } = await api.post<Payment>(`/invoices/${invoiceId}/payments/`, payload);
  return data;
}
