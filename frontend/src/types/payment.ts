export interface Payment {
  id: number;
  invoice: number;
  invoice_number: string;
  amount: string;
  payment_date: string;
  payment_method: string;
  reference_number: string;
  performed_by: number | null;
  performed_by_name: string;
  notes: string;
}

export interface PaymentCreatePayload {
  amount: number;
  payment_method: string;
  reference_number: string;
  notes: string;
}

export interface PaymentsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Payment[];
}
