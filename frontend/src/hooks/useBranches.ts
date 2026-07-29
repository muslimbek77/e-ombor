import { useQuery } from "@tanstack/react-query";
import { branchesQueryKey, getBranches } from "../api/branches";

export function useBranches() {
  return useQuery({
    queryKey: branchesQueryKey,
    queryFn: getBranches,
    select: (response) => response.results,
  });
}
