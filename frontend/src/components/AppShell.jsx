import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/documents', label: 'Documents' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/tickets', label: 'Tickets' },
]

export default function AppShell({ title, eyebrow, subtitle, actions, children }) {
  const { user, logout } = useAuth()

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <p className="eyebrow">E-Ombor</p>
          <h2>Operatsion panel</h2>
          <span>{user?.branch_name || 'Bosh ofis'}</span>
        </div>

        <nav className="sidebar__nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar__link${isActive ? ' is-active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <strong>{user?.full_name || 'Foydalanuvchi'}</strong>
          <p>{(user?.roles || []).join(', ') || 'Rol biriktirilmagan'}</p>
          <button className="ghost-button" onClick={logout}>
            Chiqish
          </button>
        </div>
      </aside>

      <section className="app-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
          </div>
          {actions ? <div className="topbar-actions">{actions}</div> : null}
        </header>

        {children}
      </section>
    </main>
  )
}
