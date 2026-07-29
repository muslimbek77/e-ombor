import api from "../lib/axios";
import type { UsersResponse } from "../types/user";

export const usersQueryKey = ["users"] as const;

export async function getUsers(): Promise<UsersResponse> {
  const { data } = await api.get<UsersResponse>("/users/");
  return data;
}
