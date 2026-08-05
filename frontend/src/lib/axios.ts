import axios from "axios";
import type { AxiosError, AxiosRequestConfig } from "axios";

import { refresh } from "../api/auth";
import type { RefreshResponse } from "../api/auth";
import { useAuthStore } from "../stores/authStore";

interface RetryRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "ngrok-skip-browser-warning": "true" },
});

let refreshPromise: Promise<RefreshResponse> | null = null;

api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();

    if (accessToken) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryRequestConfig;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    // Don't retry twice
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    // Only handle 401
    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // Don't refresh the refresh endpoint itself
    if (originalRequest.url?.includes("/refresh")) {
      useAuthStore.getState().logout();
      window.location.href = "/";
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const store = useAuthStore.getState();

    if (!store.refreshToken) {
      store.logout();
      window.location.href = "/";
      return Promise.reject(error);
    }

    const refreshToken = store.refreshToken;

    try {
      if (!refreshPromise) {
        refreshPromise = refresh(refreshToken);
      }

      const data = await refreshPromise;

      refreshPromise = null;

      // Refresh davomida chiqib ketilgan yoki boshqa hisobga kirilgan bo'lsa,
      // eskirgan tokenni qo'llamaymiz. `data.refresh`ga tenglik — bir vaqtda
      // ketgan boshqa so'rov shu javobni allaqachon saqlab ulgurgan holat.
      const current = useAuthStore.getState().refreshToken;
      if (current !== refreshToken && current !== data.refresh) {
        return Promise.reject(error);
      }

      // Rotatsiya yoqilgan bo'lsa eski refresh token blacklist qilinadi —
      // yangisini saqlamasak, keyingi yangilashda tizimdan uchib chiqamiz.
      if (data.refresh) {
        useAuthStore.getState().setTokens(data.access, data.refresh);
      } else {
        useAuthStore.getState().setAccessToken(data.access);
      }

      originalRequest.headers = originalRequest.headers ?? {};
      originalRequest.headers.Authorization = `Bearer ${data.access}`;

      return api(originalRequest);
    } catch (err) {
      refreshPromise = null;

      useAuthStore.getState().logout();

      window.location.href = "/";

      return Promise.reject(err);
    }
  },
);

export default api;