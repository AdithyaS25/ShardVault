import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authApi } from '@/api/auth'
import { tokenStore } from '@/api/client'
import type { MeResponse as User } from '@/types'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (email: string, password: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // ── Restore session on mount via refresh cookie ──────────────────
  useEffect(() => {
    const restore = async () => {
      try {
        const { access_token } = await authApi.refresh()
        tokenStore.set(access_token)
        const me = await authApi.me()
        setUser(me)
      } catch {
        tokenStore.clear()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    restore()
  }, [])

  // ── Forced logout when 401 after refresh fails ───────────────────
  useEffect(() => {
    const handler = () => {
      tokenStore.clear()
      setUser(null)
    }
    window.addEventListener('auth:expired', handler)
    return () => window.removeEventListener('auth:expired', handler)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authApi.login({ email, password })
    tokenStore.set(access_token)
    const me = await authApi.me()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await authApi.register({ email, password })
    // Auto-login after successful registration
    await login(email, password)
  }, [login])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      register,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}