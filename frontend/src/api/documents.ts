import api from "../lib/axios";
import type {
  AppDocument,
  DocumentCreatePayload,
  DocumentFilesResponse,
  DocumentUpdatePayload,
  DocumentsResponse,
  WorkflowActionPayload,
} from "../types/document";

export const documentsQueryKey = ["documents"] as const;
export const documentQueryKey = (documentId: number) => [...documentsQueryKey, documentId] as const;
export const documentFilesQueryKey = (documentId: number) => [...documentQueryKey(documentId), "files"] as const;

export interface DocumentFilters {
  doc_type?: string;
  status?: string;
  archived?: "true" | "false" | "all";
  search?: string;
}

export async function getDocuments(filters?: DocumentFilters): Promise<DocumentsResponse> {
  const { data } = await api.get<DocumentsResponse>("/documents/", { params: filters });
  return data;
}

export async function getDocument(documentId: number): Promise<AppDocument> {
  const { data } = await api.get<AppDocument>(`/documents/${documentId}/`);
  return data;
}

export async function createDocument(payload: DocumentCreatePayload): Promise<AppDocument> {
  const { data } = await api.post<AppDocument>("/documents/", payload);
  return data;
}

export async function updateDocument({ documentId, payload }: { documentId: number; payload: DocumentUpdatePayload }): Promise<AppDocument> {
  const { data } = await api.put<AppDocument>(`/documents/${documentId}/`, payload);
  return data;
}

export async function performWorkflowAction({ documentId, payload }: { documentId: number; payload: WorkflowActionPayload }): Promise<AppDocument> {
  const { data } = await api.post<AppDocument>(`/documents/${documentId}/workflow/`, payload);
  return data;
}

export async function toggleArchive({ documentId, archive }: { documentId: number; archive: boolean }): Promise<AppDocument> {
  const { data } = await api.post<AppDocument>(`/documents/${documentId}/archive/`, { archive });
  return data;
}

export async function getDocumentFiles(documentId: number): Promise<DocumentFilesResponse> {
  const { data } = await api.get<DocumentFilesResponse>(`/documents/${documentId}/files/list/`);
  return data;
}

export async function uploadDocumentFile({ documentId, file }: { documentId: number; file: File }): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await api.post(`/documents/${documentId}/files/`, formData, { headers: { "Content-Type": "multipart/form-data" } });
}

export async function exportDocuments(filters?: Pick<DocumentFilters, "doc_type" | "status" | "archived">): Promise<Blob> {
  const { data } = await api.get<Blob>("/documents/export/", { params: filters, responseType: "blob" });
  return data;
}
