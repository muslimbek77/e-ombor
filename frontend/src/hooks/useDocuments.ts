import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createDocument,
  documentFilesQueryKey,
  documentQueryKey,
  documentsQueryKey,
  getDocument,
  getDocumentFiles,
  getDocuments,
  performWorkflowAction,
  toggleArchive,
  updateDocument,
  uploadDocumentFile,
} from "../api/documents";
import type { DocumentFilters } from "../api/documents";

export function useDocuments(filters?: DocumentFilters) {
  return useQuery({
    queryKey: filters ? [...documentsQueryKey, filters] : documentsQueryKey,
    queryFn: () => getDocuments(filters),
    select: (response) => response.results,
  });
}

export function useDocument(documentId: number) {
  return useQuery({
    queryKey: documentQueryKey(documentId),
    queryFn: () => getDocument(documentId),
    enabled: Number.isInteger(documentId) && documentId > 0,
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsQueryKey }),
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateDocument,
    onSuccess: (document) => {
      queryClient.setQueryData(documentQueryKey(document.id), document);
      return queryClient.invalidateQueries({ queryKey: documentsQueryKey });
    },
  });
}

export function useWorkflowAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: performWorkflowAction,
    onSuccess: (document) => {
      queryClient.setQueryData(documentQueryKey(document.id), document);
      return queryClient.invalidateQueries({ queryKey: documentsQueryKey });
    },
  });
}

export function useToggleArchive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: toggleArchive,
    onSuccess: (document) => {
      queryClient.setQueryData(documentQueryKey(document.id), document);
      return queryClient.invalidateQueries({ queryKey: documentsQueryKey });
    },
  });
}

export function useDocumentFiles(documentId: number) {
  return useQuery({
    queryKey: documentFilesQueryKey(documentId),
    queryFn: () => getDocumentFiles(documentId),
    select: (response) => response.results,
    enabled: Number.isInteger(documentId) && documentId > 0,
  });
}

export function useUploadDocumentFile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadDocumentFile,
    onSuccess: (_, variables) => queryClient.invalidateQueries({ queryKey: documentFilesQueryKey(variables.documentId) }),
  });
}
