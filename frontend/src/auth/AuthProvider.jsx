import { useCallback, useEffect, useMemo, useState } from 'react'

import { api, setCsrfToken } from '../lib/api'
import { AuthContext } from './auth-context'

// status: 'loading' | 'anonymous' | 'authenticated'
export default function AuthProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', user: null })

  // On page load, ask the server whether the cookie still holds a valid session.
  useEffect(() => {
    let cancelled = false
    api('/api/v1/auth/me')
      .then((data) => {
        if (cancelled) return
        setCsrfToken(data.csrf_token)
        setState({ status: 'authenticated', user: data.user })
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'anonymous', user: null })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await api('/api/v1/auth/login', { method: 'POST', body: { email, password } })
    setCsrfToken(data.csrf_token)
    setState({ status: 'authenticated', user: data.user })
  }, [])

  const logout = useCallback(async () => {
    try {
      await api('/api/v1/auth/logout', { method: 'POST' })
    } finally {
      setCsrfToken(null)
      setState({ status: 'anonymous', user: null })
    }
  }, [])

  const value = useMemo(() => ({ ...state, login, logout }), [state, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}