import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { logout as logoutRequest } from "../../api/auth";
import { queryClient } from "../../lib/queryClient";
import { useAuthStore } from "../../stores/authStore";

/**
 * Chiqish: avval serverga xabar beramiz (refresh token blacklist qilinsin),
 * keyin mahalliy holatni tozalaymiz.
 *
 * So'rov muvaffaqiyatsiz bo'lsa ham foydalanuvchi baribir chiqariladi — aks
 * holda internet uzilganda yoki server javob bermaganda tizimda qamalib qoladi.
 */
export const useLogout = () => {
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.logout);

  const mutation = useMutation({
    mutationFn: async () => {
      const { refreshToken } = useAuthStore.getState();
      if (!refreshToken) return;

      await logoutRequest(refreshToken);
    },
    onSettled: () => {
      clearAuth();
      // Keshni ham tozalaymiz, aks holda bitta kompyuterda keyingi kirgan
      // foydalanuvchi avvalgisining ma'lumotlarini ko'rib qolishi mumkin.
      queryClient.clear();
      navigate("/login", { replace: true });
    },
  });

  return mutation;
};
