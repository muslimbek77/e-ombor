import api from "../lib/axios";
import type { Invoice, InvoiceCreatePayload, InvoiceUpdatePayload, InvoicesResponse } from "../types/invoice";

export const invoicesQueryKey = ["invoices"] as const;
export const invoiceQueryKey = (invoiceId: number) => [...invoicesQueryKey, invoiceId] as const;

export async function getInvoices(): Promise<InvoicesResponse> {
  const { data } = await api.get<InvoicesResponse>("/invoices/");
  return data;
}

export async function getInvoice(invoiceId: number): Promise<Invoice> {
  const { data } = await api.get<Invoice>(`/invoices/${invoiceId}/`);
  return data;
}

export async function createInvoice(payload: InvoiceCreatePayload): Promise<Invoice> {
  const { data } = await api.post<Invoice>("/invoices/", payload);
  return data;
}

export async function updateInvoice({ invoiceId, payload }: { invoiceId: number; payload: InvoiceUpdatePayload }): Promise<Invoice> {
  const { data } = await api.put<Invoice>(`/invoices/${invoiceId}/`, payload);
  return data;
}
