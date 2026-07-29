export interface Contract {
  id: number;
  document: number;
  document_doc_number: string;
  supplier: number;
  supplier_name: string;
  contract_number: string;
  signed_date: string;
  start_date: string;
  end_date: string;
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
  contract_number: string;
  document_doc_number: string;
  supplier_name: string;
  contract_date: string;
  amount: number;
}
