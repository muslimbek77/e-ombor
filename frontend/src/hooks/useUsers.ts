import { useQuery } from "@tanstack/react-query";
import { getUsers, usersQueryKey } from "../api/users";

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
