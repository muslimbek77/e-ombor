export interface InventoryItem {
  id: number;
  warehouse: number;
  warehouse_name: string;
  branch_name: string;
  material: number;
  material_name: string;
  material_code: string;
  quantity: string;
  min_quantity: string;
  updated_at: string;
  is_low_stock: boolean;
}

export interface InventoryItemPayload {
  warehouse: number;
  material: number;
  quantity: number;
  min_quantity: number;
}

export interface InventoryAdjustmentPayload {
  quantity_delta?: number;
  min_quantity?: number;
  notes?: string;
}

export interface InventoryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: InventoryItem[];
}
