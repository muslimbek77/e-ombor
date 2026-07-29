export type PaymentStatus = "unpaid" | "partial" | "paid";

export interface Invoice {
  id: number;
  document: number;
  document_doc_number: string;
  contract: number | null;
  contract_number: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string | null;
  total_amount: string;
  paid_amount: string;
  remaining_amount: string;
  payment_status: PaymentStatus;
  payment_status_display: string;
}

export interface InvoiceCreatePayload {
  document: number;
  contract: number | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string | null;
  total_amount: number;
}

export interface InvoiceUpdatePayload {
  document: number;
  contract: number | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string | null;
  total_amount: number;
}

export interface InvoicesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Invoice[];
}
