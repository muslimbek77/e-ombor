export interface PurchaseOrderItem {
  id: number;
  purchase_order: number;
  material: number;
  material_name: string;
  quantity: string;
  unit_price: string;
  total_price: string;
}

export interface PurchaseOrderItemInput {
  material: number;
  quantity: number;
  unit_price: number;
  total_price?: number;
}

export interface PurchaseOrder {
  id: number;
  document: number;
  doc_number: string;
  title: string;
  doc_status: string;
  total_amount: string;
  supplier: number | null;
  supplier_name: string | null;
  items: PurchaseOrderItem[];
  created_at: string;
}

export interface PurchaseOrderCreatePayload {
  document: number;
  supplier: number | null;
  items: PurchaseOrderItemInput[];
}

export interface PurchaseOrderUpdatePayload {
  supplier: number | null;
  items: PurchaseOrderItemInput[];
}

export interface PurchaseOrdersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PurchaseOrder[];
}
