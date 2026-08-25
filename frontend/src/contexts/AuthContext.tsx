import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { adminApi, authApi } from '../api/endpoints'
import type { CurrentUser } from '../api/types'
import { tokenStorage } from '../lib/apiClient'

interface AuthContextValue {
  user: CurrentUser | null
  isLoading: boolean
  login: (email: string, password: string, tenantSlug: string) => Promise<void>
  registerTenant: (payload: {
    tenant_name: string
    tenant_slug: string
    admin_email: string
    admin_password: string
    admin_full_name: string
  }) => Promise<void>
  logout: () => void
  hasPermission: (code: string) => boolean
  impersonate: (userId: string) => Promise<void>
  stopImpersonating: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = async () => {
    if (!tokenStorage.getAccessToken()) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const me = await authApi.me()
      setUser(me)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (email: string, password: string, tenantSlug: string) => {
    const tokens = await authApi.login({ email, password, tenant_slug: tenantSlug })
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    await loadUser()
  }

  const registerTenant: AuthContextValue['registerTenant'] = async (payload) => {
    const tokens = await authApi.registerTenant(payload)
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    await loadUser()
  }

  const logout = () => {
    tokenStorage.clear()
    setUser(null)
  }

  const hasPermission = (code: string) => user?.permissions.includes(code) ?? false

  // Switching identity mid-session can leave every cached list/detail query
  // holding the previous user's view of the data (different permissions can
  // mean different results even within the same tenant), so both directions
  // clear the query cache before re-hydrating from /me.
  const impersonate = async (userId: string) => {
    const { access_token } = await adminApi.impersonateUser(userId)
    tokenStorage.beginImpersonation(access_token)
    queryClient.clear()
    await loadUser()
  }

  const stopImpersonating = async () => {
    tokenStorage.endImpersonation()
    queryClient.clear()
    await loadUser()
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, registerTenant, logout, hasPermission, impersonate, stopImpersonating }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
