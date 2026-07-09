const ACCESS_TOKEN_KEY = 'eombor_access_token'
const REFRESH_TOKEN_KEY = 'eombor_refresh_token'

export function getStoredTokens() {
  return {
    access: localStorage.getItem(ACCESS_TOKEN_KEY) || '',
    refresh: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
  }
}

export function storeTokens({ access = '', refresh = '' }) {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
  }

  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export async function apiFetch(path, options = {}) {
  const { access } = getStoredTokens()
  const { auth = true, ...fetchOptions } = options
  const headers = new Headers(fetchOptions.headers || {})

  if (!headers.has('Content-Type') && fetchOptions.body && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (auth && access) {
    headers.set('Authorization', `Bearer ${access}`)
  }

  const response = await fetch(path, {
    ...fetchOptions,
    headers,
  })

  if (response.status === 204) {
    return null
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.error ||
      data?.message ||
      (typeof data === 'object' ? Object.values(data).flat().join(' ') : 'So‘rovda xatolik yuz berdi')

    throw new Error(message)
  }

  return data
}

export async function apiDownload(path, filename, options = {}) {
  const { access } = getStoredTokens()
  const { auth = true } = options
  const headers = new Headers()

  if (auth && access) {
    headers.set('Authorization', `Bearer ${access}`)
  }

  const response = await fetch(path, { headers })
  if (!response.ok) {
    throw new Error('Faylni yuklab olishda xatolik yuz berdi')
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
