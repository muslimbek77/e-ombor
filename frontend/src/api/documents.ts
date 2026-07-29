import api from "../lib/axios";

export interface Document {
  id: number;
  doc_number: string;
  doc_type: string;
  title: string;
  status: string;
}

export interface DocumentsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Document[];
}

export const documentsQueryKey = ["documents"] as const;

export async function getDocuments(): Promise<DocumentsResponse> {
  const { data } = await api.get<DocumentsResponse>("/documents/");
  return data;
}
