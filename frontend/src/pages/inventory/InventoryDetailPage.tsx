import { AlertTriangle, ArrowLeft, ArrowLeftRight, Building2, Calendar, Layers, SlidersHorizontal, Tag, X } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAdjustInventoryItem, useInventoryItem } from "../../hooks/useInventory";
import { useCreateStockMovement, useStockMovements } from "../../hooks/useStockMovements";
import { AdjustStockForm } from "./AdjustStockForm";
import { MovementForm } from "./MovementForm";
import { formatDateTime } from "../tickets/ticketUtils";
import type { InventoryAdjustmentPayload } from "../../types/inventory";
import type { StockMovementCreatePayload } from "../../types/stockMovement";

export default function InventoryDetailPage() {
  const { id } = useParams();
  const itemId = Number(id);
  const [isAdjustOpen, setIsAdjustOpen] = useState(false);
  const [isMovementOpen, setIsMovementOpen] = useState(false);

  const { data: item, isPending, isError } = useInventoryItem(itemId);
  const adjustInventoryItem = useAdjustInventoryItem();
  const createStockMovement = useCreateStockMovement();
  const { data: movements = [], isPending: isMovementsPending } = useStockMovements(item ? { warehouse: item.warehouse, material: item.material } : undefined);

  if (!Number.isInteger(itemId) || itemId < 1) return <DetailState>Inventar ID noto'g'ri.</DetailState>;
  if (isPending) return <DetailState>Yuklanmoqda...</DetailState>;
  if (isError || !item) return <DetailState>Zaxira yozuvini topib bo'lmadi.</DetailState>;

  return (
    <main className="min-h-full bg-gray-50 p-6">
      <div className="mx-auto max-w-3xl space-y-5">
        <Link to="/inventory" className="inline-flex items-center gap-2 text-sm font-semibold text-gray-600 hover:text-green-700">
          <ArrowLeft size={16} /> Inventarga qaytish
        </Link>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{item.material_name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600"><Tag size={11} /> {item.material_code}</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600"><Building2 size={11} /> {item.warehouse_name}</span>
                {item.is_low_stock && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600"><AlertTriangle size={12} /> Kam qoldiq</span>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button type="button" onClick={() => setIsMovementOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
                <ArrowLeftRight size={15} /> Harakat qo'shish
              </button>
              <button type="button" onClick={() => setIsAdjustOpen(true)} className="inline-flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700">
                <SlidersHorizontal size={15} /> Miqdorni tuzatish
              </button>
            </div>
          </div>

          <dl className="grid gap-4 sm:grid-cols-2">
            <InfoField icon={<Layers size={17} />} label="Joriy miqdor" value={item.quantity} />
            <InfoField icon={<AlertTriangle size={17} />} label="Minimal zaxira" value={item.min_quantity} />
            <InfoField icon={<Building2 size={17} />} label="Filial" value={item.branch_name} />
            <InfoField icon={<Calendar size={17} />} label="Yangilangan sana" value={formatDateTime(item.updated_at)} />
          </dl>
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-bold text-gray-900">Harakatlar tarixi</h2>
          {isMovementsPending && <p className="text-sm text-gray-400">Yuklanmoqda...</p>}
          {!isMovementsPending && movements.length === 0 && <p className="text-sm text-gray-400">Harakatlar yo'q</p>}
          {!isMovementsPending && movements.length > 0 && (
            <div className="space-y-3">
              {movements.map((movement) => (
                <div key={movement.id} className="flex flex-wrap items-start justify-between gap-3 rounded-xl bg-gray-50 p-4">
                  <div className="flex items-start gap-3">
                    <span className={`mt-0.5 ${movement.movement_type === "OUT" ? "text-red-600" : "text-green-600"}`}><ArrowLeftRight size={17} /></span>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{movement.movement_type_display} · {movement.quantity}</p>
                      <p className="text-xs text-gray-500">
                        {movement.warehouse_name}
                        {movement.target_warehouse_name ? ` → ${movement.target_warehouse_name}` : ""}
                      </p>
                      {movement.notes && <p className="mt-1 text-xs text-gray-500">{movement.notes}</p>}
                    </div>
                  </div>
                  <div className="text-right text-xs text-gray-400">
                    <p>{formatDateTime(movement.performed_at)}</p>
                    <p className="mt-0.5">{movement.performed_by_name}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {isAdjustOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="adjust-inventory-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <h2 id="adjust-inventory-title" className="text-xl font-bold text-gray-900">Miqdorni tuzatish</h2>
              <button type="button" aria-label="Yopish" onClick={() => setIsAdjustOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {adjustInventoryItem.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Miqdorni saqlab bo'lmadi.</p>}
            <AdjustStockForm
              item={item}
              isSubmitting={adjustInventoryItem.isPending}
              onCancel={() => setIsAdjustOpen(false)}
              onSubmit={(payload: InventoryAdjustmentPayload) => adjustInventoryItem.mutate({ itemId: item.id, payload }, { onSuccess: () => setIsAdjustOpen(false) })}
            />
          </div>
        </div>
      )}

      {isMovementOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="create-movement-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between gap-4">
              <h2 id="create-movement-title" className="text-xl font-bold text-gray-900">Yangi harakat</h2>
              <button type="button" aria-label="Yopish" onClick={() => setIsMovementOpen(false)} className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"><X size={18} /></button>
            </div>
            {createStockMovement.isError && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">Harakatni saqlab bo'lmadi. Miqdorni va omborni tekshirib qayta urinib ko'ring.</p>}
            <MovementForm
              item={item}
              isSubmitting={createStockMovement.isPending}
              onCancel={() => setIsMovementOpen(false)}
              onSubmit={(payload: StockMovementCreatePayload) => createStockMovement.mutate(payload, { onSuccess: () => setIsMovementOpen(false) })}
            />
          </div>
        </div>
      )}
    </main>
  );
}

function InfoField({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex gap-3 rounded-xl bg-gray-50 p-4">
      <span className="mt-0.5 text-gray-400">{icon}</span>
      <div>
        <dt className="text-xs font-medium text-gray-500">{label}</dt>
        <dd className="mt-1 text-sm font-semibold text-gray-800">{value}</dd>
      </div>
    </div>
  );
}

function DetailState({ children }: { children: React.ReactNode }) {
  return <main className="flex min-h-full items-center justify-center bg-gray-50 p-6 text-sm text-gray-500">{children}</main>;
}
