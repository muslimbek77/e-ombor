import api from "../lib/axios";
import type { Address, AddressPayload, AddressesResponse } from "../types/address";

export const addressesQueryKey = ["addresses"] as const;
export const addressQueryKey = (addressId: number) => [...addressesQueryKey, addressId] as const;

export async function getAddresses(): Promise<AddressesResponse> {
  const { data } = await api.get<AddressesResponse>("/addresses/");
  return data;
}

export async function createAddress(payload: AddressPayload): Promise<Address> {
  const { data } = await api.post<Address>("/addresses/", payload);
  return data;
}

export async function getAddress(addressId: number): Promise<Address> {
  const { data } = await api.get<Address>(`/addresses/${addressId}/`);
  return data;
}

export async function updateAddress({ addressId, payload }: { addressId: number; payload: AddressPayload }): Promise<Address> {
  const { data } = await api.put<Address>(`/addresses/${addressId}/`, payload);
  return data;
}

export async function deleteAddress(addressId: number): Promise<void> {
  await api.delete(`/addresses/${addressId}/`);
}
