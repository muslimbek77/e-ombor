import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    const success = await login({ username, password })
    if (!success) {
      setError('Login yoki parol noto'g'ri')
    }
  }

  return (
    <main className="page-container">
      <div className="card">
        <h1>E-Ombor tizimiga kirish</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Login
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Parol
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="error">{error}</div>}
          <button type="submit">Kirish</button>
        </form>
      </div>
    </main>
  )
}
