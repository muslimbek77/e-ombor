import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { login, authLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login({ email, password })
    } catch (requestError) {
      setError(requestError.message || "Login yoki parol noto'g'ri")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-hero">
        <div className="hero-badge">Ko&apos;prikqurilish AJ</div>
        <h1>E-Ombor boshqaruv markazi</h1>
        <p>
          Xaridlar, ombor, obyektlar va ichki murojaatlarni bitta panelda kuzatish uchun
          tizimga kiring.
        </p>
        <div className="hero-points">
          <span>Workflow nazorati</span>
          <span>Ombor qoldig&apos;i</span>
          <span>Filial kesimidagi ko&apos;rinish</span>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-card__header">
          <p className="eyebrow">Tizimga kirish</p>
          <h2>Hisobingiz bilan davom eting</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="user@company.uz"
              autoComplete="email"
            />
          </label>

          <label>
            Parol
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Kamida 8 ta belgi"
              autoComplete="current-password"
            />
          </label>

          {error && <div className="error-banner">{error}</div>}

          <button type="submit" disabled={isSubmitting || authLoading}>
            {isSubmitting ? 'Tekshirilmoqda...' : 'Kirish'}
          </button>
        </form>
      </section>
    </main>
  )
}
