import api from "../lib/axios";
import type { Notification, NotificationsResponse } from "../types/notification";

export const notificationsQueryKey = ["notifications"] as const;

export async function getNotifications(): Promise<NotificationsResponse> {
  const { data } = await api.get<NotificationsResponse>("/notifications/");
  return data;
}

export async function markNotificationRead(notificationId: number): Promise<Notification> {
  const { data } = await api.post<Notification>(`/notifications/${notificationId}/read/`);
  return data;
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post("/notifications/read-all/");
}
