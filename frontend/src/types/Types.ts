export interface KPICard {
  title: string;
  value: string;
  change: number;
  icon: string;
  color: string;
  description: string;
}

export interface PurchaseRequest {
  id: string;
  number: string;
  object: string;
  requester: string;
  amount: number;
  status: RequestStatus;
  date: string;
}

export type RequestStatus =
  | 'yaratildi'
  | 'arxivda'
  | 'rais_tasdig'
  | 'tasdiqlandi'
  | 'tolovda'
  | 'yetkazilmoqda'
  | 'yakunlandi'
  | 'rad_etildi';

export interface PendingDocument {
  id: string;
  number: string;
  object: string;
  amount: number;
  approver: string;
  type: string;
}

export interface LowStockMaterial {
  id: string;
  name: string;
  stock: number;
  minLevel: number;
  unit: string;
}

export interface ActivityItem {
  id: string;
  type: 'new_request' | 'approved' | 'payment' | 'received' | 'issued';
  description: string;
  time: string;
  user: string;
}

export interface BranchPerformance {
  id: string;
  name: string;
  activeObjects: number;
  budget: number;
  spent: number;
}

export interface MonthlyData {
  month: string;
  kirim: number;
  chiqim: number;
  qoldiq: number;
}

export interface BudgetData {
  month: string;
  byudjet: number;
  xarajat: number;
}