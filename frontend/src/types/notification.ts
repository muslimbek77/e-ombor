export interface Notification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  notification_type: string;
  related_type: string | null;
  related_id: number | null;
  created_at: string;
}

export interface NotificationsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notification[];
}
