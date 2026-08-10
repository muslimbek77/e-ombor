export type DocType = "purchase_request" | "contract" | "invoice";

/** Zanjir manbasi — `backend/api/workflow.py`. */
export type DocStatus =
  | "created"
  | "revision"
  | "architecture"
  | "ceo"
  | "procurement"
  | "anticorruption"
  | "accountant"
  | "delivering"
  | "received"
  | "closed"
  | "rejected";

export type WorkflowAction = "submit" | "approve" | "advance" | "close" | "reject" | "return" | "send_back" | "reopen";

export interface DocumentApproval {
  id: number;
  action: string;
  comment: string;
  created_at: string;
  approver: number | null;
  approver_name: string;
  approver_roles: string[];
  /** Faqat `send_back` da to'ladi: qaysi bosqichga qaytarilgani. */
  target_status: string;
  target_status_display: string;
}

/** `send_back` da tanlanadigan bosqich — ro'yxatni server beradi. */
export interface SendBackTarget {
  value: DocStatus;
  label: string;
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
  send_back_targets: SendBackTarget[];
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
  /** Faqat `advance` uchun: xarid qatorlari qaysi omborga kirim bo'ladi. */
  warehouse?: number;
  /** Faqat `send_back` uchun: qaysi oldingi bosqichga qaytariladi. */
  target_status?: DocStatus;
}

export interface DocumentComment {
  id: number;
  document: number;
  text: string;
  author: number | null;
  author_name: string;
  created_at: string;
}

export interface DocumentCommentsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: DocumentComment[];
}
