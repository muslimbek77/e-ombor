export type DocType = "purchase_request" | "contract" | "invoice";

export type DocStatus =
  | "created"
  | "architecture"
  | "ceo"
  | "approved"
  | "contract"
  | "payment"
  | "delivering"
  | "received"
  | "closed"
  | "rejected";

export type WorkflowAction = "submit" | "approve" | "advance" | "close" | "reject" | "reopen";

export interface DocumentApproval {
  id: number;
  action: string;
  comment: string;
  created_at: string;
  approver: number | null;
  approver_name: string;
}

export interface AppDocument {
  id: number;
  doc_number: string;
  doc_type: DocType;
  status: DocStatus;
  status_display: string;
  title: string;
  description: string;
  created_by: number | null;
  created_by_name: string;
  site: number | null;
  site_name: string;
  branch: number | null;
  branch_name: string;
  total_amount: string;
  notes: string;
  is_archived: boolean;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
  approvals: DocumentApproval[];
  allowed_actions: WorkflowAction[];
  can_archive: boolean;
}

export interface DocumentCreatePayload {
  doc_type: DocType;
  title: string;
  description: string;
  site: number | null;
  total_amount: number;
  notes: string;
}

export interface DocumentUpdatePayload {
  doc_type: DocType;
  title: string;
  description: string;
  site: number | null;
  total_amount: number;
  notes: string;
}

export interface DocumentsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AppDocument[];
}

export interface DocumentFile {
  id: number;
  document: number;
  file: string;
  original_filename: string;
  file_size: number;
  uploaded_by: number | null;
  uploaded_by_name: string;
  created_at: string;
}

export interface DocumentFilesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: DocumentFile[];
}

export interface WorkflowActionPayload {
  action: WorkflowAction;
  comment?: string;
}
