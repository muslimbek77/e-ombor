import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createUser, deleteUser, getUser, getUsers, updateUser, userQueryKey, usersQueryKey } from "../api/users";

export function useUsers() {
  return useQuery({
    queryKey: usersQueryKey,
    queryFn: getUsers,
    select: (response) => response.results,
    retry: false,
  });
}

export function useProrabs() {
  const { data: users, ...rest } = useUsers();
  return { ...rest, data: users?.filter((user) => user.roles.includes("prorab")) };
}

export function useUser(userId: number) {
  return useQuery({
    queryKey: userQueryKey(userId),
    queryFn: () => getUser(userId),
    enabled: Number.isInteger(userId) && userId > 0,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: usersQueryKey }),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateUser,
    onSuccess: (user) => {
      queryClient.setQueryData(userQueryKey(user.id), user);
      return queryClient.invalidateQueries({ queryKey: usersQueryKey });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteUser,
    onSuccess: (_, userId) => {
      queryClient.removeQueries({ queryKey: userQueryKey(userId) });
      return queryClient.invalidateQueries({ queryKey: usersQueryKey });
    },
  });
}
