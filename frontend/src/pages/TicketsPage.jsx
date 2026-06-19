import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../auth/AuthContext'
import { formatDate, normalizeResults } from '../lib/format'

export default function TicketsPage() {
  const { apiFetch, apiDownload } = useAuth()
  const [tickets, setTickets] = useState([])
  const [sites, setSites] = useState([])
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    category: '',
  })
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [busyKey, setBusyKey] = useState('')
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    category: 'material_shortage',
    priority: 'medium',
    site: '',
  })

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

  useEffect(() => {
    const loadSites = async () => {
      try {
        const data = await apiFetch('/api/sites/')
        setSites(normalizeResults(data))
      } catch (requestError) {
        // Lookup failure should not block page rendering.
      }
    }

    loadSites()
  }, [apiFetch])

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

  const handleCreateTicket = async (event) => {
    event.preventDefault()
    setBusyKey('create-ticket')
    setError('')
    setSuccessMessage('')
    try {
      await apiFetch('/api/tickets/', {
        method: 'POST',
        body: JSON.stringify({
          title: createForm.title,
          description: createForm.description,
          category: createForm.category,
          priority: createForm.priority,
          site: createForm.site || null,
        }),
      })
      setCreateForm({
        title: '',
        description: '',
        category: 'material_shortage',
        priority: 'medium',
        site: '',
      })
      setSuccessMessage('Yangi murojaat yaratildi.')
      await loadTickets()
    } catch (requestError) {
      setError(requestError.message || 'Murojaat yaratishda xatolik yuz berdi.')
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
      {successMessage ? <div className="success-banner">{successMessage}</div> : null}

      <section className="panel page-filters">
        <div className="panel__header">
          <h3>Yangi murojaat</h3>
          <span>Create flow</span>
        </div>
        <form className="filters-grid" onSubmit={handleCreateTicket}>
          <input
            value={createForm.title}
            onChange={(event) => setCreateForm((current) => ({ ...current, title: event.target.value }))}
            placeholder="Murojaat sarlavhasi"
            required
          />
          <input
            value={createForm.description}
            onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
            placeholder="Muammo tavsifi"
            required
          />
          <select
            value={createForm.category}
            onChange={(event) => setCreateForm((current) => ({ ...current, category: event.target.value }))}
          >
            <option value="material_shortage">Material yetishmasligi</option>
            <option value="equipment">Texnika kerak</option>
            <option value="labor">Ishchi kuchi</option>
            <option value="other">Boshqa</option>
          </select>
          <select
            value={createForm.priority}
            onChange={(event) => setCreateForm((current) => ({ ...current, priority: event.target.value }))}
          >
            <option value="low">Past</option>
            <option value="medium">O‘rta</option>
            <option value="high">Yuqori</option>
            <option value="urgent">Shoshilinch</option>
          </select>
          <select
            value={createForm.site}
            onChange={(event) => setCreateForm((current) => ({ ...current, site: event.target.value }))}
          >
            <option value="">Obyektsiz</option>
            {sites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name}
              </option>
            ))}
          </select>
          <button type="submit" className="tiny-button" disabled={busyKey === 'create-ticket'}>
            Yaratish
          </button>
        </form>
      </section>

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
