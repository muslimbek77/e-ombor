import { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiDownload, apiFetch, getStoredTokens, storeTokens } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [tokens, setTokens] = useState(getStoredTokens)

  useEffect(() => {
    const loadProfile = async () => {
      if (!tokens.access) {
        setUser(null)
        setAuthLoading(false)
        return
      }

      try {
        const profile = await apiFetch('/api/auth/user/')
        setUser(profile)
      } catch (error) {
        storeTokens({ access: '', refresh: '' })
        setTokens({ access: '', refresh: '' })
        setUser(null)
      } finally {
        setAuthLoading(false)
      }
    }

    loadProfile()
  }, [tokens.access])

  const login = async ({ email, password }) => {
    const data = await apiFetch('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    const nextTokens = { access: data.access, refresh: data.refresh }
    storeTokens(nextTokens)
    setTokens(nextTokens)
    setUser(data.user)
    navigate('/dashboard')
  }

  const logout = async () => {
    try {
      if (tokens.refresh) {
        await apiFetch('/api/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh: tokens.refresh }),
        })
      }
    } catch (error) {
      // Frontend cleanup is enough even if server-side blacklist call fails.
    }

    storeTokens({ access: '', refresh: '' })
    setTokens({ access: '', refresh: '' })
    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, authLoading, apiFetch, apiDownload }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
