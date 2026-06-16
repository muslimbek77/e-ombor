import { useAuth } from '../auth/AuthContext'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <main className="page-container">
      <div className="card">
        <div className="header-row">
          <h1>Dashboard</h1>
          <button onClick={logout}>Chiqish</button>
        </div>
        <p>Xush kelibsiz, {user?.username}</p>
        <p>Bu birinchi bosqich uchun placeholder sahifadir.</p>
      </div>
    </main>
  )
}
