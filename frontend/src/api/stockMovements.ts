import api from "../lib/axios";
import type {
  StockMovement,
  StockMovementCreatePayload,
  StockMovementsResponse,
} from "../types/stockMovement";

export const stockMovementsQueryKey = ["stock-movements"] as const;

export interface StockMovementFilters {
  warehouse?: number;
  material?: number;
  movement_type?: string;
}

export async function getStockMovements(filters?: StockMovementFilters): Promise<StockMovementsResponse> {
  const { data } = await api.get<StockMovementsResponse>("/stock-movements/", { params: filters });
  return data;
}

export async function createStockMovement(payload: StockMovementCreatePayload): Promise<StockMovement> {
  const { data } = await api.post<StockMovement>("/stock-movements/", payload);
  return data;
}
