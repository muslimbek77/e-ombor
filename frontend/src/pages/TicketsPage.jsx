import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../auth/AuthContext'
import { formatDate, normalizeResults } from '../lib/format'

export default function TicketsPage() {
  const { apiFetch, apiDownload } = useAuth()
  const [tickets, setTickets] = useState([])
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    category: '',
  })
  const [error, setError] = useState('')
  const [busyKey, setBusyKey] = useState('')

  const loadTickets = async () => {
    setError('')
    try {
      const params = new URLSearchParams()
      if (filters.status) params.set('status', filters.status)
      if (filters.priority) params.set('priority', filters.priority)
      if (filters.category) params.set('category', filters.category)
      const data = await apiFetch(`/api/tickets/?${params.toString()}`)
      setTickets(normalizeResults(data))
    } catch (requestError) {
      setError(requestError.message || 'Murojaatlarni olishda xatolik yuz berdi.')
    }
  }

  useEffect(() => {
    loadTickets()
  }, [filters.status, filters.priority, filters.category])

  const handleExport = async () => {
    setBusyKey('export-tickets')
    setError('')
    try {
      const params = new URLSearchParams()
      if (filters.status) params.set('status', filters.status)
      if (filters.priority) params.set('priority', filters.priority)
      if (filters.category) params.set('category', filters.category)
      await apiDownload(`/api/tickets/export/?${params.toString()}`, 'tickets-export.csv')
    } catch (requestError) {
      setError(requestError.message || 'Eksportda xatolik yuz berdi.')
    } finally {
      setBusyKey('')
    }
  }

  return (
    <AppShell
      eyebrow="Murojaatlar moduli"
      title="Tickets"
      subtitle="Filial murojaatlari va ularning ustuvorligi"
      actions={
        <button className="tiny-button" disabled={busyKey === 'export-tickets'} onClick={handleExport}>
          CSV eksport
        </button>
      }
    >
      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel page-filters">
        <div className="filters-grid">
          <select
            value={filters.status}
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
          >
            <option value="">Barcha statuslar</option>
            <option value="open">Ochiq</option>
            <option value="in_progress">Jarayonda</option>
            <option value="resolved">Yechildi</option>
            <option value="closed">Yopildi</option>
          </select>
          <select
            value={filters.priority}
            onChange={(event) => setFilters((current) => ({ ...current, priority: event.target.value }))}
          >
            <option value="">Barcha ustuvorliklar</option>
            <option value="low">Past</option>
            <option value="medium">O‘rta</option>
            <option value="high">Yuqori</option>
            <option value="urgent">Shoshilinch</option>
          </select>
          <select
            value={filters.category}
            onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}
          >
            <option value="">Barcha kategoriyalar</option>
            <option value="material_shortage">Material yetishmasligi</option>
            <option value="equipment">Texnika kerak</option>
            <option value="labor">Ishchi kuchi</option>
            <option value="other">Boshqa</option>
          </select>
        </div>
      </section>

      <section className="panel">
        <div className="panel__header">
          <h3>Murojaatlar ro‘yxati</h3>
          <span>{tickets.length} ta</span>
        </div>
        <div className="table-list">
          {tickets.map((ticket) => (
            <div key={ticket.id} className="table-row">
              <div>
                <strong>{ticket.title}</strong>
                <p>{ticket.description}</p>
                <p>
                  {ticket.branch_name || 'Filialsiz'} • {ticket.site_name || 'Obyektsiz'} • {formatDate(ticket.created_at)}
                </p>
              </div>
              <div className="table-row__actions">
                <span className="badge">{ticket.status_display}</span>
                <span className="badge">{ticket.priority_display}</span>
                <span className="badge">{ticket.category_display}</span>
              </div>
            </div>
          ))}
          {!tickets.length ? <p className="empty-state">Murojaatlar topilmadi.</p> : null}
        </div>
      </section>
    </AppShell>
  )
}
