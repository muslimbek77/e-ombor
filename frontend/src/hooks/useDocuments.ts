import { useQuery } from "@tanstack/react-query";
import { documentsQueryKey, getDocuments } from "../api/documents";

export function useDocuments() {
  return useQuery({
    queryKey: documentsQueryKey,
    queryFn: getDocuments,
    select: (response) => response.results,
  });
}
