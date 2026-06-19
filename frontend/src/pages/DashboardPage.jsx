import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../auth/AuthContext'
import { formatCurrency, formatDate, normalizeResults } from '../lib/format'

const WORKFLOW_ACTION_LABELS = {
  submit: 'Arxitekturaga yuborish',
  approve: 'Tasdiqlash',
  advance: 'Keyingi bosqichga o‘tkazish',
  close: 'Yopish',
  reject: 'Rad etish',
  reopen: 'Qayta ochish',
}

export default function DashboardPage() {
  const { apiFetch, apiDownload } = useAuth()
  const [dashboard, setDashboard] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [documents, setDocuments] = useState([])
  const [archivedDocuments, setArchivedDocuments] = useState([])
  const [inventory, setInventory] = useState([])
  const [sites, setSites] = useState([])
  const [tickets, setTickets] = useState([])
  const [movements, setMovements] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [workflowDrafts, setWorkflowDrafts] = useState({})
  const [inventoryDrafts, setInventoryDrafts] = useState({})
  const [busyKey, setBusyKey] = useState('')

  const loadData = async () => {
    setLoading(true)
    setError('')

    try {
      const [
        dashboardData,
        analyticsData,
        documentData,
        archivedDocumentData,
        inventoryData,
        siteData,
        ticketData,
        movementData,
        auditData,
      ] = await Promise.all([
        apiFetch('/api/dashboard/'),
        apiFetch('/api/analytics/overview/'),
        apiFetch('/api/documents/'),
        apiFetch('/api/documents/?archived=true'),
        apiFetch('/api/inventory/'),
        apiFetch('/api/sites/'),
        apiFetch('/api/tickets/'),
        apiFetch('/api/stock-movements/'),
        apiFetch('/api/audit-logs/'),
      ])

      setDashboard(dashboardData)
      setAnalytics(analyticsData)
      setDocuments(normalizeResults(documentData).slice(0, 6))
      setArchivedDocuments(normalizeResults(archivedDocumentData).slice(0, 6))
      setInventory(normalizeResults(inventoryData).slice(0, 6))
      setSites(normalizeResults(siteData).slice(0, 5))
      setTickets(normalizeResults(ticketData).slice(0, 5))
      setMovements(normalizeResults(movementData).slice(0, 6))
      setAuditLogs(normalizeResults(auditData).slice(0, 8))
    } catch (requestError) {
      setError(requestError.message || 'Dashboard ma’lumotlarini olishda xatolik yuz berdi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [apiFetch])

  const handleWorkflowChange = (documentId, field, value) => {
    setWorkflowDrafts((current) => ({
      ...current,
      [documentId]: {
        ...current[documentId],
        [field]: value,
      },
    }))
  }

  const handleArchiveToggle = async (documentId, archive) => {
    setBusyKey(`archive-${documentId}`)
    setError('')
    setSuccessMessage('')

    try {
      await apiFetch(`/api/documents/${documentId}/archive/`, {
        method: 'POST',
        body: JSON.stringify({ archive }),
      })
      setSuccessMessage(archive ? 'Hujjat arxivga olindi.' : 'Hujjat arxivdan chiqarildi.')
      await loadData()
    } catch (requestError) {
      setError(requestError.message || 'Hujjat arxiv holatini yangilashda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleWorkflowSubmit = async (documentId, fallbackAction) => {
    const draft = workflowDrafts[documentId] || {}
    const action = draft.action || fallbackAction
    if (!action) return

    setBusyKey(`workflow-${documentId}`)
    setError('')
    setSuccessMessage('')

    try {
      await apiFetch(`/api/documents/${documentId}/workflow/`, {
        method: 'POST',
        body: JSON.stringify({
          action,
          comment: draft.comment || '',
        }),
      })
      setSuccessMessage('Hujjat holati muvaffaqiyatli yangilandi.')
      setWorkflowDrafts((current) => ({ ...current, [documentId]: { action: '', comment: '' } }))
      await loadData()
    } catch (requestError) {
      setError(requestError.message || 'Workflow amalini bajarishda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleInventoryDraft = (itemId, field, value) => {
    setInventoryDrafts((current) => ({
      ...current,
      [itemId]: {
        ...current[itemId],
        [field]: value,
      },
    }))
  }

  const handleInventorySubmit = async (itemId) => {
    const draft = inventoryDrafts[itemId] || {}
    setBusyKey(`inventory-${itemId}`)
    setError('')
    setSuccessMessage('')

    try {
      await apiFetch(`/api/inventory/${itemId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          quantity_delta: Number(draft.quantity_delta || 0),
          min_quantity: draft.min_quantity === '' || draft.min_quantity == null ? undefined : Number(draft.min_quantity),
          notes: draft.notes || '',
        }),
      })
      setSuccessMessage('Ombor qoldig‘i muvaffaqiyatli yangilandi.')
      setInventoryDrafts((current) => ({ ...current, [itemId]: { quantity_delta: '', min_quantity: '', notes: '' } }))
      await loadData()
    } catch (requestError) {
      setError(requestError.message || 'Qoldiqni yangilashda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleMarkAllRead = async () => {
    setBusyKey('notifications')
    setError('')
    setSuccessMessage('')

    try {
      await apiFetch('/api/notifications/read-all/', { method: 'POST' })
      setSuccessMessage('Bildirishnomalar o‘qilgan deb belgilandi.')
      await loadData()
    } catch (requestError) {
      setError(requestError.message || 'Bildirishnomalarni yangilashda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleExport = async (kind) => {
    setBusyKey(`export-${kind}`)
    setError('')
    setSuccessMessage('')

    const exportMap = {
      documents: ['/api/documents/export/?archived=all', 'documents-export.csv'],
      inventory: ['/api/inventory/export/', 'inventory-export.csv'],
      tickets: ['/api/tickets/export/', 'tickets-export.csv'],
    }

    try {
      const [path, filename] = exportMap[kind]
      await apiDownload(path, filename)
      setSuccessMessage('Eksport fayli yuklab olindi.')
    } catch (requestError) {
      setError(requestError.message || 'Eksport qilishda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  const lowStockItems = inventory.filter((item) => item.is_low_stock)
  const statusBreakdown = dashboard?.document_status_breakdown || []
  const paymentSummary = dashboard?.payment_summary || {}
  const notifications = dashboard?.notifications || []
  const overdueInvoices = analytics?.overdue_invoices || []
  const documentsByType = analytics?.documents_by_type || []

  return (
    <AppShell
      eyebrow="E-Ombor nazorat paneli"
      title="Dashboard"
      subtitle="Filial, ombor va workflow ko‘rsatkichlari"
    >

      {error && <div className="error-banner">{error}</div>}
      {successMessage && <div className="success-banner">{successMessage}</div>}

      <section className="hero-panel">
        <div>
          <p className="hero-panel__label">Joriy holat</p>
          <h2>Filial, ombor va workflow ko&apos;rsatkichlari bir joyda</h2>
          <p>
            E-IMZO va 1C tashqarida qoldirilgan holda, tizimning asosiy operatsion ko&apos;rinishi
            ishchi holatga keltirildi.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <span>Invoice</span>
            <strong>{formatCurrency(paymentSummary.total_invoiced)}</strong>
          </div>
          <div>
            <span>To&apos;langan</span>
            <strong>{formatCurrency(paymentSummary.total_paid)}</strong>
          </div>
          <div>
            <span>Qoldiq</span>
            <strong>{formatCurrency(paymentSummary.remaining)}</strong>
          </div>
          <div className="hero-actions">
            <button className="tiny-button" disabled={busyKey === 'export-documents'} onClick={() => handleExport('documents')}>
              Hujjatlar CSV
            </button>
            <button className="tiny-button" disabled={busyKey === 'export-inventory'} onClick={() => handleExport('inventory')}>
              Inventory CSV
            </button>
            <button className="tiny-button" disabled={busyKey === 'export-tickets'} onClick={() => handleExport('tickets')}>
              Ticket CSV
            </button>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <span>Hujjatlar</span>
          <strong>{loading ? '...' : dashboard?.total_documents ?? 0}</strong>
        </article>
        <article className="stat-card">
          <span>Tasdiq kutmoqda</span>
          <strong>{loading ? '...' : dashboard?.pending_approvals ?? 0}</strong>
        </article>
        <article className="stat-card">
          <span>Omborlar</span>
          <strong>{loading ? '...' : dashboard?.total_warehouses ?? 0}</strong>
        </article>
        <article className="stat-card warning">
          <span>Kam zaxira</span>
          <strong>{loading ? '...' : dashboard?.low_stock_items ?? 0}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="panel">
          <div className="panel__header">
            <h3>Workflow holatlari</h3>
            <span>{statusBreakdown.length} status</span>
          </div>
          <div className="status-list">
            {statusBreakdown.map((item) => (
              <div key={item.status} className="status-pill">
                <span>{item.status}</span>
                <strong>{item.total}</strong>
              </div>
            ))}
            {!statusBreakdown.length && <p className="empty-state">Hali hujjatlar mavjud emas.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Bildirishnomalar</h3>
            <button
              className="tiny-button"
              disabled={busyKey === 'notifications' || !notifications.length}
              onClick={handleMarkAllRead}
            >
              Hammasini o‘qildi qilish
            </button>
          </div>
          <div className="stack-list">
            {notifications.map((item) => (
              <div key={item.id} className="feed-item">
                <strong>{item.title}</strong>
                <p>{item.message}</p>
                <time>{formatDate(item.created_at)}</time>
              </div>
            ))}
            {!notifications.length && <p className="empty-state">Yangi bildirishnoma yo&apos;q.</p>}
          </div>
        </article>

        <article className="panel panel--wide">
          <div className="panel__header">
            <h3>Hujjatlar va workflow</h3>
            <span>{documents.length} ta yozuv</span>
          </div>
          <div className="table-list">
            {documents.map((doc) => (
              <div key={doc.id} className="table-row table-row--stretch">
                <div className="table-row__content">
                  <strong>{doc.doc_number}</strong>
                  <p>{doc.title}</p>
                </div>
                <div className="table-row__actions">
                  <span className="badge">{doc.status_display}</span>
                  <time>{formatDate(doc.created_at)}</time>
                  {doc.allowed_actions?.length > 0 && (
                    <div className="action-box">
                      <select
                        value={workflowDrafts[doc.id]?.action || doc.allowed_actions[0]}
                        onChange={(event) => handleWorkflowChange(doc.id, 'action', event.target.value)}
                      >
                        {doc.allowed_actions.map((action) => (
                          <option key={action} value={action}>
                            {WORKFLOW_ACTION_LABELS[action] || action}
                          </option>
                        ))}
                      </select>
                      <input
                        value={workflowDrafts[doc.id]?.comment || ''}
                        onChange={(event) => handleWorkflowChange(doc.id, 'comment', event.target.value)}
                        placeholder="Izoh yoki rad sababi"
                      />
                      <button
                        className="tiny-button"
                        disabled={busyKey === `workflow-${doc.id}`}
                        onClick={() =>
                          handleWorkflowSubmit(doc.id, doc.allowed_actions[0])
                        }
                      >
                        Amalni bajarish
                      </button>
                      {doc.can_archive && (
                        <button
                          className="tiny-button"
                          disabled={busyKey === `archive-${doc.id}`}
                          onClick={() => handleArchiveToggle(doc.id, true)}
                        >
                          Arxivga olish
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {!documents.length && <p className="empty-state">Hujjatlar topilmadi.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Arxiv hujjatlar</h3>
            <span>{archivedDocuments.length} ta</span>
          </div>
          <div className="stack-list">
            {archivedDocuments.map((doc) => (
              <div key={doc.id} className="feed-item compact">
                <strong>{doc.doc_number}</strong>
                <p>
                  {doc.title} • {doc.status_display}
                </p>
                {doc.can_archive && (
                  <button
                    className="tiny-button"
                    disabled={busyKey === `archive-${doc.id}`}
                    onClick={() => handleArchiveToggle(doc.id, false)}
                  >
                    Arxivdan chiqarish
                  </button>
                )}
              </div>
            ))}
            {!archivedDocuments.length && <p className="empty-state">Arxiv hujjatlar yo‘q.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Ombor qoldig‘i boshqaruvi</h3>
            <span>{inventory.length} ta</span>
          </div>
          <div className="stack-list">
            {inventory.map((item) => (
              <div key={item.id} className="feed-item compact">
                <strong>{item.material_name}</strong>
                <p>
                  {item.warehouse_name}: {item.quantity} / min {item.min_quantity}
                </p>
                <div className="inline-form">
                  <input
                    type="number"
                    step="0.001"
                    value={inventoryDrafts[item.id]?.quantity_delta || ''}
                    onChange={(event) => handleInventoryDraft(item.id, 'quantity_delta', event.target.value)}
                    placeholder="+/- miqdor"
                  />
                  <input
                    type="number"
                    step="0.001"
                    value={inventoryDrafts[item.id]?.min_quantity || ''}
                    onChange={(event) => handleInventoryDraft(item.id, 'min_quantity', event.target.value)}
                    placeholder="Yangi minimum"
                  />
                  <button
                    className="tiny-button"
                    disabled={busyKey === `inventory-${item.id}`}
                    onClick={() => handleInventorySubmit(item.id)}
                  >
                    Saqlash
                  </button>
                </div>
              </div>
            ))}
            {!inventory.length && <p className="empty-state">Inventar topilmadi.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Qurilish obyektlari</h3>
            <span>{sites.length} ta</span>
          </div>
          <div className="stack-list">
            {sites.map((site) => (
              <div key={site.id} className="feed-item compact">
                <strong>{site.name}</strong>
                <p>
                  {site.status_display} • Byudjet: {formatCurrency(site.budget)}
                </p>
              </div>
            ))}
            {!sites.length && <p className="empty-state">Obyektlar mavjud emas.</p>}
          </div>
        </article>

        <article className="panel panel--wide">
          <div className="panel__header">
            <h3>Murojaatlar va audit</h3>
            <span>Nazorat paneli</span>
          </div>
          <div className="dual-column">
            <div className="stack-list">
              {tickets.map((ticket) => (
                <div key={ticket.id} className="feed-item compact">
                  <strong>{ticket.title}</strong>
                  <p>
                    {ticket.priority_display} • {ticket.status_display}
                  </p>
                </div>
              ))}
              {!tickets.length && <p className="empty-state">Murojaatlar topilmadi.</p>}
            </div>

            <div className="stack-list">
              {auditLogs.map((log) => (
                <div key={log.id} className="feed-item compact">
                  <strong>{log.action}</strong>
                  <p>
                    {log.model_name} • {log.user_name || 'System'} • {formatDate(log.created_at)}
                  </p>
                </div>
              ))}
              {!auditLogs.length && <p className="empty-state">Audit yozuvlari topilmadi.</p>}
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Muddati o‘tgan invoice</h3>
            <span>{overdueInvoices.length} ta</span>
          </div>
          <div className="stack-list">
            {overdueInvoices.map((invoice) => (
              <div key={invoice.id} className="feed-item compact">
                <strong>{invoice.invoice_number}</strong>
                <p>
                  {invoice.payment_status_display} • Qoldiq: {formatCurrency(invoice.remaining_amount)}
                </p>
              </div>
            ))}
            {!overdueInvoices.length && <p className="empty-state">Muddati o‘tgan invoice yo‘q.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h3>Hujjat turlari kesimi</h3>
            <span>{documentsByType.length} ta tur</span>
          </div>
          <div className="status-list">
            {documentsByType.map((item) => (
              <div key={item.doc_type} className="status-pill">
                <span>{item.doc_type}</span>
                <strong>{item.total}</strong>
              </div>
            ))}
            {!documentsByType.length && <p className="empty-state">Ma’lumot topilmadi.</p>}
          </div>
        </article>

        <article className="panel panel--wide">
          <div className="panel__header">
            <h3>Ombor harakati</h3>
            <span>{movements.length} ta</span>
          </div>
          <div className="table-list">
            {movements.map((movement) => (
              <div key={movement.id} className="table-row">
                <div>
                  <strong>{movement.material_name}</strong>
                  <p>{movement.warehouse_name}</p>
                </div>
                <div>
                  <span className="badge">{movement.movement_type_display}</span>
                  <time>{movement.quantity}</time>
                </div>
              </div>
            ))}
            {!movements.length && <p className="empty-state">Harakatlar tarixi topilmadi.</p>}
          </div>
        </article>
      </section>
    </AppShell>
  )
}
