// auth.ts
import axios from "axios";

import api from "../lib/axios";

const authApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "ngrok-skip-browser-warning": "true" },
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

// Refresh token'ni serverda blacklist qiladi. Bu bo'lmasa, chiqilgandan keyin
// ham o'g'irlangan token bilan yangi access token olish mumkin bo'lib qolaveradi.
export const logout = async (refreshToken: string) => {
  const { data } = await api.post<{ message: string }>("/auth/logout/", {
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
