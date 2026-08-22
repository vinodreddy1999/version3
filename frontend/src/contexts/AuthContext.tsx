import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { authApi } from '../api/endpoints'
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
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
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

  return (
    <AuthContext.Provider value={{ user, isLoading, login, registerTenant, logout, hasPermission }}>
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
