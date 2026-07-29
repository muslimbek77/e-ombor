import api from "../lib/axios";
import type { BranchesResponse } from "../types/branch";

export const branchesQueryKey = ["branches"] as const;

export async function getBranches(): Promise<BranchesResponse> {
  const { data } = await api.get<BranchesResponse>("/branches/");
  return data;
}
