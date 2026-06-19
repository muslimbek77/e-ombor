import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../auth/AuthContext'
import { formatDate, normalizeResults } from '../lib/format'

export default function InventoryPage() {
  const { apiFetch, apiDownload } = useAuth()
  const [items, setItems] = useState([])
  const [filters, setFilters] = useState({ material: '' })
  const [drafts, setDrafts] = useState({})
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [busyKey, setBusyKey] = useState('')

  const loadInventory = async () => {
    setError('')
    try {
      const params = new URLSearchParams()
      if (filters.material) params.set('material', filters.material)
      const data = await apiFetch(`/api/inventory/?${params.toString()}`)
      setItems(normalizeResults(data))
    } catch (requestError) {
      setError(requestError.message || 'Inventory ma’lumotlarini olishda xatolik yuz berdi.')
    }
  }

  useEffect(() => {
    loadInventory()
  }, [])

  const handleDraft = (id, field, value) => {
    setDrafts((current) => ({
      ...current,
      [id]: {
        ...current[id],
        [field]: value,
      },
    }))
  }

  const handleSubmit = async (id) => {
    const draft = drafts[id] || {}
    setBusyKey(`inventory-${id}`)
    setError('')
    setSuccessMessage('')
    try {
      await apiFetch(`/api/inventory/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          quantity_delta: Number(draft.quantity_delta || 0),
          min_quantity: draft.min_quantity === '' || draft.min_quantity == null ? undefined : Number(draft.min_quantity),
          notes: draft.notes || '',
        }),
      })
      setSuccessMessage('Inventory muvaffaqiyatli yangilandi.')
      await loadInventory()
    } catch (requestError) {
      setError(requestError.message || 'Inventory yangilanmadi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleExport = async () => {
    setBusyKey('export-inventory')
    setError('')
    try {
      await apiDownload('/api/inventory/export/', 'inventory-export.csv')
    } catch (requestError) {
      setError(requestError.message || 'Eksportda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  return (
    <AppShell
      eyebrow="Ombor moduli"
      title="Inventory"
      subtitle="Qoldiq, minimum va tezkor tuzatishlar"
      actions={
        <button className="tiny-button" disabled={busyKey === 'export-inventory'} onClick={handleExport}>
          CSV eksport
        </button>
      }
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {successMessage ? <div className="success-banner">{successMessage}</div> : null}

      <section className="panel">
        <div className="panel__header">
          <h3>Inventar yozuvlari</h3>
          <span>{items.length} ta</span>
        </div>
        <div className="table-list">
          {items.map((item) => (
            <div key={item.id} className="table-row table-row--stretch">
              <div className="table-row__content">
                <strong>{item.material_name}</strong>
                <p>{item.warehouse_name}</p>
                <p>
                  Joriy: {item.quantity} • Min: {item.min_quantity} • Yangilangan: {formatDate(item.updated_at)}
                </p>
              </div>
              <div className="table-row__actions">
                {item.is_low_stock ? <span className="badge">Kam zaxira</span> : null}
                <div className="inline-form">
                  <input
                    type="number"
                    step="0.001"
                    value={drafts[item.id]?.quantity_delta || ''}
                    onChange={(event) => handleDraft(item.id, 'quantity_delta', event.target.value)}
                    placeholder="+/- miqdor"
                  />
                  <input
                    type="number"
                    step="0.001"
                    value={drafts[item.id]?.min_quantity || ''}
                    onChange={(event) => handleDraft(item.id, 'min_quantity', event.target.value)}
                    placeholder="Yangi minimum"
                  />
                  <input
                    value={drafts[item.id]?.notes || ''}
                    onChange={(event) => handleDraft(item.id, 'notes', event.target.value)}
                    placeholder="Izoh"
                  />
                  <button
                    className="tiny-button"
                    disabled={busyKey === `inventory-${item.id}`}
                    onClick={() => handleSubmit(item.id)}
                  >
                    Saqlash
                  </button>
                </div>
              </div>
            </div>
          ))}
          {!items.length ? <p className="empty-state">Inventar yozuvlari topilmadi.</p> : null}
        </div>
      </section>
    </AppShell>
  )
}
