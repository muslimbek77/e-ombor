export interface Material {
  id: number;
  name: string;
  code: string;
  unit: string;
  category: string;
  description: string;
  created_at: string;
}

export interface MaterialPayload {
  name: string;
  code: string;
  unit: string;
  category: string;
  description: string;
}

export interface MaterialsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Material[];
}
