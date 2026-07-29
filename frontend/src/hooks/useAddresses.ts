import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { addressQueryKey, addressesQueryKey, createAddress, deleteAddress, getAddress, getAddresses, updateAddress } from "../api/addresses";

export function useAddresses() {
  return useQuery({
    queryKey: addressesQueryKey,
    queryFn: getAddresses,
    select: (response) => response.results,
  });
}

export function useCreateAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAddress,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: addressesQueryKey }),
  });
}

export function useAddress(addressId: number) {
  return useQuery({ queryKey: addressQueryKey(addressId), queryFn: () => getAddress(addressId), enabled: Number.isInteger(addressId) && addressId > 0 });
}

export function useUpdateAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateAddress,
    onSuccess: (address) => {
      queryClient.setQueryData(addressQueryKey(address.id), address);
      return queryClient.invalidateQueries({ queryKey: addressesQueryKey });
    },
  });
}

export function useDeleteAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAddress,
    onSuccess: (_, addressId) => {
      queryClient.removeQueries({ queryKey: addressQueryKey(addressId) });
      return queryClient.invalidateQueries({ queryKey: addressesQueryKey });
    },
  });
}
