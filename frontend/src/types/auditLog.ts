export interface AuditLog {
  id: number;
  user: number | null;
  user_name: string | null;
  action: string;
  model_name: string;
  object_id: number | null;
  /** Obyektning o'qiladigan nomi; o'chirilgan obyektlarda `null` — o'rniga id ko'rsatiladi. */
  object_label: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AuditLog[];
}
