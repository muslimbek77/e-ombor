import api from "../lib/axios";
import type {
  Contract,
  ContractPayload,
  ContractsResponse,
} from "../types/shartnoma";

export const contractsQueryKey = ["contracts"] as const;
export const contractQueryKey = (contractId: number) =>
  [...contractsQueryKey, contractId] as const;

export async function getContracts(): Promise<ContractsResponse> {
  const { data } = await api.get<ContractsResponse>("/contracts/");
  return data;
}

export async function getContract(contractId: number): Promise<Contract> {
  const { data } = await api.get<Contract>(`/contracts/${contractId}/`);
  return data;
}

export async function createContract(
  payload: ContractPayload,
): Promise<Contract> {
  const { data } = await api.post<Contract>("/contracts/", payload);
  return data;
}

export async function updateContract({
  contractId,
  payload,
}: {
  contractId: number;
  payload: ContractPayload;
}): Promise<Contract> {
  const { data } = await api.put<Contract>(
    `/contracts/${contractId}/`,
    payload,
  );

  return data;
}

export async function deleteContract(contractId: number): Promise<void> {
  await api.delete(`/contracts/${contractId}/`);
}
