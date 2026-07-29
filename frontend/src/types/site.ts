export type SiteStatus = "active" | "paused" | "completed" | string;

export interface Site {
  id: number;
  name: string;
  code: string;
  branch: number;
  branch_name: string;
  address: string;
  status: SiteStatus;
  status_display: string;
  budget: string;
  prorab: number;
  prorab_name: string;
  created_at: string;
  updated_at: string;
}

export interface SitePayload {
  name: string;
  code: string;
  branch: number;
  address: string;
  status: SiteStatus;
  budget: string;
  prorab: number;
}

export interface SitesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Site[];
}
