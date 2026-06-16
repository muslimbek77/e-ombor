import { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('eombor_token') || '')

  useEffect(() => {
    if (token) {
      localStorage.setItem('eombor_token', token)
      fetch('/api/auth/user/', {
        headers: {
          Authorization: `Token ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data?.id) {
            setUser(data)
          } else {
            setUser(null)
            setToken('')
          }
        })
    }
  }, [token])

  const login = async ({ username, password }) => {
    const response = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })
    if (!response.ok) return false
    const data = await response.json()
    setToken(data.token)
    setUser(data.user)
    navigate('/dashboard')
    return true
  }

  const logout = () => {
    setToken('')
    setUser(null)
    localStorage.removeItem('eombor_token')
    navigate('/login')
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
