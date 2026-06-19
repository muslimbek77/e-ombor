import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../auth/AuthContext'
import { formatCurrency, formatDate, normalizeResults } from '../lib/format'

const WORKFLOW_ACTION_LABELS = {
  submit: 'Arxitekturaga yuborish',
  approve: 'Tasdiqlash',
  advance: 'Keyingi bosqich',
  close: 'Yopish',
  reject: 'Rad etish',
  reopen: 'Qayta ochish',
}

export default function DocumentsPage() {
  const { apiFetch, apiDownload } = useAuth()
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [busyKey, setBusyKey] = useState('')
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    docType: '',
    archived: 'false',
  })
  const [workflowDrafts, setWorkflowDrafts] = useState({})

  const loadDocuments = async () => {
    setError('')
    try {
      const params = new URLSearchParams()
      if (filters.search) params.set('search', filters.search)
      if (filters.status) params.set('status', filters.status)
      if (filters.docType) params.set('doc_type', filters.docType)
      params.set('archived', filters.archived)

      const data = await apiFetch(`/api/documents/?${params.toString()}`)
      setDocuments(normalizeResults(data))
    } catch (requestError) {
      setError(requestError.message || 'Hujjatlarni olishda xatolik yuz berdi.')
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [filters.archived, filters.status, filters.docType])

  const handleSearchSubmit = async (event) => {
    event.preventDefault()
    await loadDocuments()
  }

  const handleWorkflowChange = (documentId, field, value) => {
    setWorkflowDrafts((current) => ({
      ...current,
      [documentId]: {
        ...current[documentId],
        [field]: value,
      },
    }))
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
      setSuccessMessage('Workflow amali bajarildi.')
      await loadDocuments()
    } catch (requestError) {
      setError(requestError.message || 'Workflow amalida xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
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
      await loadDocuments()
    } catch (requestError) {
      setError(requestError.message || 'Arxiv amali bajarilmadi.')
    } finally {
      setBusyKey('')
    }
  }

  const handleExport = async () => {
    setBusyKey('export-documents')
    setError('')
    try {
      const params = new URLSearchParams()
      if (filters.status) params.set('status', filters.status)
      if (filters.docType) params.set('doc_type', filters.docType)
      params.set('archived', filters.archived)
      await apiDownload(`/api/documents/export/?${params.toString()}`, 'documents-export.csv')
    } catch (requestError) {
      setError(requestError.message || 'Eksportda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  return (
    <AppShell
      eyebrow="Hujjatlar moduli"
      title="Documents"
      subtitle="Qidirish, workflow va arxiv boshqaruvi"
      actions={
        <button className="tiny-button" disabled={busyKey === 'export-documents'} onClick={handleExport}>
          CSV eksport
        </button>
      }
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {successMessage ? <div className="success-banner">{successMessage}</div> : null}

      <section className="panel page-filters">
        <form className="filters-grid" onSubmit={handleSearchSubmit}>
          <input
            value={filters.search}
            onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
            placeholder="Raqam, sarlavha yoki tavsif bo‘yicha qidirish"
          />
          <select
            value={filters.docType}
            onChange={(event) => setFilters((current) => ({ ...current, docType: event.target.value }))}
          >
            <option value="">Barcha turlar</option>
            <option value="purchase_request">Purchase request</option>
            <option value="contract">Contract</option>
            <option value="invoice">Invoice</option>
          </select>
          <select
            value={filters.status}
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
          >
            <option value="">Barcha statuslar</option>
            <option value="created">Yaratildi</option>
            <option value="architecture">Arxitekturada</option>
            <option value="ceo">Raisda</option>
            <option value="approved">Tasdiqlandi</option>
            <option value="contract">Shartnomada</option>
            <option value="payment">To‘lovda</option>
            <option value="delivering">Yetkazilmoqda</option>
            <option value="received">Qabul qilindi</option>
            <option value="closed">Yopildi</option>
            <option value="rejected">Rad etildi</option>
          </select>
          <select
            value={filters.archived}
            onChange={(event) => setFilters((current) => ({ ...current, archived: event.target.value }))}
          >
            <option value="false">Faol hujjatlar</option>
            <option value="true">Arxiv hujjatlar</option>
            <option value="all">Barchasi</option>
          </select>
          <button type="submit" className="tiny-button">
            Qidirish
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel__header">
          <h3>Hujjatlar ro‘yxati</h3>
          <span>{documents.length} ta</span>
        </div>
        <div className="table-list">
          {documents.map((doc) => (
            <div key={doc.id} className="table-row table-row--stretch">
              <div className="table-row__content">
                <strong>{doc.doc_number}</strong>
                <p>{doc.title}</p>
                <p>
                  {doc.branch_name || 'Filialsiz'} • {doc.site_name || 'Obyektsiz'} • {formatCurrency(doc.total_amount)}
                </p>
              </div>
              <div className="table-row__actions">
                <span className="badge">{doc.status_display}</span>
                <time>{formatDate(doc.created_at)}</time>
                {doc.allowed_actions?.length ? (
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
                      placeholder="Izoh"
                    />
                    <button
                      className="tiny-button"
                      disabled={busyKey === `workflow-${doc.id}`}
                      onClick={() => handleWorkflowSubmit(doc.id, doc.allowed_actions[0])}
                    >
                      Amalni bajarish
                    </button>
                  </div>
                ) : null}
                {doc.can_archive ? (
                  <button
                    className="tiny-button"
                    disabled={busyKey === `archive-${doc.id}`}
                    onClick={() => handleArchiveToggle(doc.id, !doc.is_archived)}
                  >
                    {doc.is_archived ? 'Arxivdan chiqarish' : 'Arxivga olish'}
                  </button>
                ) : null}
              </div>
            </div>
          ))}
          {!documents.length ? <p className="empty-state">Mos hujjatlar topilmadi.</p> : null}
        </div>
      </section>
    </AppShell>
  )
}
