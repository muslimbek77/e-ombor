export interface Warehouse {
  id: number;
  name: string;
  code: string;
  branch: number;
  branch_name: string;
  address: string;
  min_stock_alert: boolean;
  created_at: string;
}

export interface WarehousePayload {
  name: string;
  code: string;
  branch: number;
  address: string;
  min_stock_alert: boolean;
}

export interface WarehousesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Warehouse[];
}
