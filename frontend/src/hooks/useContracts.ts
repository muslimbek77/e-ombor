import { useQuery } from "@tanstack/react-query";
import {
  getContracts,
  contractsQueryKey,
  contractQueryKey,
  getContract,
} from "../api/contracts";
import type { ContractsResponse, Contract } from "../types/shartnoma";

export function useContracts() {
  return useQuery<ContractsResponse, Error, Contract[]>({
    queryKey: contractsQueryKey,
    queryFn: getContracts,
    select: (response) => response.results,
  });
}
export function useContract(contractId: number) {
  return useQuery<Contract, Error>({
    queryKey: contractQueryKey(contractId),
    queryFn: () => getContract(contractId),
    enabled: Number.isInteger(contractId) && contractId > 0,
  });
}
