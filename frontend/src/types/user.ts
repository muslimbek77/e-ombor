export interface AppUser {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  stir_inn: string;
  roles: string[];
  branch: number | null;
  branch_name: string;
  is_active: boolean;
  is_staff: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface UsersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AppUser[];
}
