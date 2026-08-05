export interface Contract {
  id: number;
  document: number;
  document_doc_number: string;
  supplier: number | null;
  supplier_name: string;
  contract_number: string;
  signed_date: string | null;
  start_date: string | null;
  end_date: string | null;
  total_amount: string;
  description: string;
}

export interface ContractsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Contract[];
}
export interface ContractPayload {
  document: number;
  supplier: number | null;
  contract_number: string;
  signed_date: string | null;
  start_date: string | null;
  end_date: string | null;
  total_amount: number;
  description: string;
}
