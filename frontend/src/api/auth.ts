// auth.ts
import axios from "axios";

import api from "../lib/axios";

const authApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
}

export const login = async (payload: LoginPayload) => {
  const { data } = await authApi.post("/auth/login/", payload);
  return data;
};

export const refresh = async (refreshToken: string) => {
  const { data } = await authApi.post("/auth/refresh/", {
    refresh: refreshToken,
  });

  return data;
};

// Authenticated request — goes through the shared `api` instance, not `authApi`.
export const changePassword = async (payload: ChangePasswordPayload) => {
  const { data } = await api.post<{ message: string }>(
    "/auth/change-password/",
    payload,
  );

  return data;
};
