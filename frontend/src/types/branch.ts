export interface Branch {
  id: number;
  name: string;
  code: string;
  address: string;
  phone: string;
  is_active: boolean;
  created_at: string;
}

export interface BranchesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Branch[];
}
