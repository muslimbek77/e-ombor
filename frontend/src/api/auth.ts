// auth.ts
import axios from "axios";

const authApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

export interface LoginPayload {
  email: string;
  password: string;
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
