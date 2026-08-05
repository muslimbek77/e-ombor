export type MovementType = "IN" | "OUT" | "TRANSFER";

export interface StockMovement {
  id: number;
  warehouse: number;
  warehouse_name: string;
  target_warehouse: number | null;
  target_warehouse_name: string | null;
  material: number;
  material_name: string;
  movement_type: MovementType;
  movement_type_display: string;
  quantity: string;
  reference_doc: number | null;
  performed_by: number | null;
  performed_by_name: string;
  performed_at: string;
  notes: string;
}

export interface StockMovementCreatePayload {
  warehouse: number;
  target_warehouse?: number | null;
  material: number;
  movement_type: MovementType;
  quantity: number;
  notes?: string;
}

export interface StockMovementsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StockMovement[];
}
