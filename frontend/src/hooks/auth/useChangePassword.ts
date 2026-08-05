import { useMutation } from "@tanstack/react-query";
import { changePassword } from "../../api/auth";

export const useChangePassword = () => {
  return useMutation({
    mutationFn: changePassword,
  });
};
