import type { PurchaseRequest, PendingDocument, LowStockMaterial, ActivityItem, BranchPerformance, MonthlyData, BudgetData } from './types';

export const purchaseRequests: PurchaseRequest[] = [
  { id: '1', number: 'XS-2025-0412', object: 'Chirchiq ko\'prik loyihasi', requester: 'A. Toshmatov', amount: 145_000_000, status: 'tolovda', date: '2025-06-20' },
  { id: '2', number: 'XS-2025-0411', object: 'Fergana magistral yo\'li', requester: 'B. Rahimov', amount: 89_500_000, status: 'rais_tasdig', date: '2025-06-19' },
  { id: '3', number: 'XS-2025-0410', object: 'Samarqand tunnel', requester: 'D. Yusupova', amount: 312_000_000, status: 'tasdiqlandi', date: '2025-06-18' },
  { id: '4', number: 'XS-2025-0409', object: 'Namangan yo\'l tarmog\'i', requester: 'F. Mirzayev', amount: 67_800_000, status: 'yetkazilmoqda', date: '2025-06-17' },
  { id: '5', number: 'XS-2025-0408', object: 'Andijon by-pass', requester: 'H. Qodirov', amount: 224_500_000, status: 'yakunlandi', date: '2025-06-16' },
  { id: '6', number: 'XS-2025-0407', object: 'Toshkent halqa yo\'li', requester: 'M. Sodiqov', amount: 98_200_000, status: 'rad_etildi', date: '2025-06-15' },
];

export const pendingDocuments: PendingDocument[] = [
  { id: '1', number: 'SH-2025-0218', object: 'Chirchiq ko\'prik loyihasi', amount: 145_000_000, approver: 'Rais o\'rinbosari', type: 'Shartnoma' },
  { id: '2', number: 'FK-2025-0119', object: 'Fergana magistral', amount: 89_500_000, approver: 'Moliya direktori', type: 'Faktura' },
  { id: '3', number: 'AK-2025-0087', object: 'Samarqand tunnel', amount: 45_000_000, approver: 'Texnik direktor', type: 'Akt' },
  { id: '4', number: 'SH-2025-0219', object: 'Toshkent halqa yo\'li', amount: 267_800_000, approver: 'Bosh direktor', type: 'Shartnoma' },
];

export const lowStockMaterials: LowStockMaterial[] = [
  { id: '1', name: 'Sement M-400', stock: 12, minLevel: 50, unit: 'tonna' },
  { id: '2', name: 'Temir armaturai Ø16', stock: 3.5, minLevel: 20, unit: 'tonna' },
  { id: '3', name: 'Qum (qurilish)', stock: 45, minLevel: 100, unit: 'm³' },
  { id: '4', name: 'Granit shebeni', stock: 8, minLevel: 30, unit: 'tonna' },
  { id: '5', name: 'Bitum BND 60/90', stock: 2.1, minLevel: 10, unit: 'tonna' },
];

export const activities: ActivityItem[] = [
  { id: '1', type: 'new_request', description: 'Namangan filiali yangi xarid so\'rovi yubordi', time: '10 daqiqa oldin', user: 'F. Mirzayev' },
  { id: '2', type: 'approved', description: 'XS-2025-0410 shartnoma tasdiqlandi', time: '45 daqiqa oldin', user: 'D. Yusupova' },
  { id: '3', type: 'payment', description: 'Chirchiq loyihasi uchun to\'lov amalga oshirildi', time: '2 soat oldin', user: 'Moliya bo\'limi' },
  { id: '4', type: 'received', description: '25 tonna sement M-400 qabul qilindi', time: '3 soat oldin', user: 'Ombor xizmati' },
  { id: '5', type: 'issued', description: 'Fergana filialiga 8 tonna armaturai chiqarildi', time: '5 soat oldin', user: 'Ombor xizmati' },
  { id: '6', type: 'approved', description: 'Andijon by-pass loyihasi yakunlandi', time: 'Kecha', user: 'H. Qodirov' },
];

export const branchPerformance: BranchPerformance[] = [
  { id: '1', name: 'Toshkent filiali', activeObjects: 8, budget: 2_400_000_000, spent: 1_872_000_000 },
  { id: '2', name: 'Samarqand filiali', activeObjects: 5, budget: 1_800_000_000, spent: 1_260_000_000 },
  { id: '3', name: 'Fergana filiali', activeObjects: 6, budget: 1_600_000_000, spent: 1_424_000_000 },
  { id: '4', name: 'Namangan filiali', activeObjects: 4, budget: 1_200_000_000, spent: 720_000_000 },
  { id: '5', name: 'Andijon filiali', activeObjects: 3, budget: 900_000_000, spent: 657_000_000 },
  { id: '6', name: 'Buxoro filiali', activeObjects: 2, budget: 600_000_000, spent: 348_000_000 },
];

export const monthlyStockData: MonthlyData[] = [
  { month: 'Yak', kirim: 420, chiqim: 380, qoldiq: 1240 },
  { month: 'Fev', kirim: 380, chiqim: 420, qoldiq: 1200 },
  { month: 'Mar', kirim: 560, chiqim: 490, qoldiq: 1270 },
  { month: 'Apr', kirim: 490, chiqim: 380, qoldiq: 1380 },
  { month: 'May', kirim: 620, chiqim: 540, qoldiq: 1460 },
  { month: 'Iyn', kirim: 580, chiqim: 610, qoldiq: 1430 },
  { month: 'Iyl', kirim: 710, chiqim: 650, qoldiq: 1490 },
  { month: 'Avg', kirim: 640, chiqim: 590, qoldiq: 1540 },
  { month: 'Sen', kirim: 520, chiqim: 480, qoldiq: 1580 },
  { month: 'Okt', kirim: 780, chiqim: 720, qoldiq: 1640 },
  { month: 'Noy', kirim: 680, chiqim: 590, qoldiq: 1730 },
  { month: 'Dek', kirim: 540, chiqim: 510, qoldiq: 1760 },
];

export const budgetData: BudgetData[] = [
  { month: 'Yan', byudjet: 800, xarajat: 720 },
  { month: 'Fev', byudjet: 750, xarajat: 680 },
  { month: 'Mar', byudjet: 900, xarajat: 850 },
  { month: 'Apr', byudjet: 850, xarajat: 790 },
  { month: 'May', byudjet: 1000, xarajat: 940 },
  { month: 'Iyn', byudjet: 950, xarajat: 1020 },
];

export const requestStatusData = [
  { name: 'Yaratildi', value: 18, color: '#6B7280' },
  { name: 'Arxivda', value: 8, color: '#8B5CF6' },
  { name: 'Rais tasdig\'ida', value: 12, color: '#F59E0B' },
  { name: 'Tasdiqlandi', value: 24, color: '#10B981' },
  { name: 'To\'lovda', value: 9, color: '#3B82F6' },
  { name: 'Yetkazilmoqda', value: 15, color: '#06B6D4' },
  { name: 'Yakunlandi', value: 31, color: '#059669' },
  { name: 'Rad etildi', value: 6, color: '#EF4444' },
];