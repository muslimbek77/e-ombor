import api from "../lib/axios";
import type { AppUser, UserCreatePayload, UserUpdatePayload, UsersResponse } from "../types/user";

export const usersQueryKey = ["users"] as const;
export const userQueryKey = (userId: number) => [...usersQueryKey, userId] as const;

export async function getUsers(): Promise<UsersResponse> {
  const { data } = await api.get<UsersResponse>("/users/");
  return data;
}

export async function getUser(userId: number): Promise<AppUser> {
  const { data } = await api.get<AppUser>(`/users/${userId}/`);
  return data;
}

export async function createUser(payload: UserCreatePayload): Promise<AppUser> {
  const { data } = await api.post<AppUser>("/users/", payload);
  return data;
}

export async function updateUser({ userId, payload }: { userId: number; payload: UserUpdatePayload }): Promise<AppUser> {
  const { data } = await api.put<AppUser>(`/users/${userId}/`, payload);
  return data;
}

export async function deleteUser(userId: number): Promise<void> {
  await api.delete(`/users/${userId}/`);
}
