/**
 * context/AuthContext.tsx — ShardVault Frontend
 * ================================================
 * Global auth state. Access token lives ONLY here in memory.
 * On mount: silently tries /auth/refresh (HttpOnly cookie flow).
 * Exposes: user, isAuthenticated, isLoading, login, logout
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from "react"
import { authApi } from "@/api/auth"
import { tokenStore } from "@/api/client"
import type { MeResponse } from "@/types"

interface AuthContextValue {
  user: MeResponse | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount — silently refresh token if cookie exists
  useEffect(() => {
    const tryRestore = async () => {
      try {
        const res = await authApi.refresh()
        tokenStore.set(res.access_token)
        setAccessToken(res.access_token)
        const me = await authApi.me()
        setUser(me)
      } catch {
        // No valid cookie — user needs to log in
        tokenStore.clear()
        setUser(null)
        setAccessToken(null)
      } finally {
        setIsLoading(false)
      }
    }
    tryRestore()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    tokenStore.set(res.access_token)
    setAccessToken(res.access_token)
    const me = await authApi.me()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Proceed regardless
    } finally {
      tokenStore.clear()
      setAccessToken(null)
      setUser(null)
    }
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const me = await authApi.me()
      setUser(me)
    } catch {
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!user && !!accessToken,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
