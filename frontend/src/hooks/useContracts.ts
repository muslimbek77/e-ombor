import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getContracts,
  contractsQueryKey,
  contractQueryKey,
  getContract,
  createContract,
  updateContract,
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

export function useCreateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createContract,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: contractsQueryKey }),
  });
}

export function useUpdateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateContract,
    onSuccess: (contract) => {
      queryClient.setQueryData(contractQueryKey(contract.id), contract);
      return queryClient.invalidateQueries({ queryKey: contractsQueryKey });
    },
  });
}
