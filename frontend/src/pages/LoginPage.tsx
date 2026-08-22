import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Button, Field, Input } from '../components/ui'

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const { login, registerTenant } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [loginForm, setLoginForm] = useState({ email: '', password: '', tenant_slug: '' })
  const [registerForm, setRegisterForm] = useState({
    tenant_name: '',
    tenant_slug: '',
    admin_email: '',
    admin_password: '',
    admin_full_name: '',
  })

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(loginForm.email, loginForm.password, loginForm.tenant_slug)
      navigate('/')
    } catch {
      setError('Invalid email, password, or organization.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await registerTenant(registerForm)
      navigate('/')
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Could not create your organization.'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-xl font-bold text-indigo-600">Metam ERP</h1>
        <div className="mb-4 flex gap-2 text-sm">
          <button
            className={`border-b-2 pb-1 ${mode === 'login' ? 'border-indigo-600 font-semibold text-indigo-600' : 'border-transparent text-slate-500'}`}
            onClick={() => setMode('login')}
          >
            Sign in
          </button>
          <button
            className={`border-b-2 pb-1 ${mode === 'register' ? 'border-indigo-600 font-semibold text-indigo-600' : 'border-transparent text-slate-500'}`}
            onClick={() => setMode('register')}
          >
            New organization
          </button>
        </div>

        {error && <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}

        {mode === 'login' ? (
          <form className="flex flex-col gap-3" onSubmit={handleLogin}>
            <Field label="Organization slug">
              <Input
                required
                value={loginForm.tenant_slug}
                onChange={(e) => setLoginForm({ ...loginForm, tenant_slug: e.target.value })}
                placeholder="acme"
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                required
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                required
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              />
            </Field>
            <Button type="submit" disabled={isSubmitting} className="mt-2">
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        ) : (
          <form className="flex flex-col gap-3" onSubmit={handleRegister}>
            <Field label="Organization name">
              <Input
                required
                value={registerForm.tenant_name}
                onChange={(e) => setRegisterForm({ ...registerForm, tenant_name: e.target.value })}
              />
            </Field>
            <Field label="Organization slug">
              <Input
                required
                pattern="[a-z0-9]+(-[a-z0-9]+)*"
                value={registerForm.tenant_slug}
                onChange={(e) => setRegisterForm({ ...registerForm, tenant_slug: e.target.value })}
                placeholder="acme"
              />
            </Field>
            <Field label="Your name">
              <Input
                required
                value={registerForm.admin_full_name}
                onChange={(e) => setRegisterForm({ ...registerForm, admin_full_name: e.target.value })}
              />
            </Field>
            <Field label="Your email">
              <Input
                type="email"
                required
                value={registerForm.admin_email}
                onChange={(e) => setRegisterForm({ ...registerForm, admin_email: e.target.value })}
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                required
                minLength={8}
                value={registerForm.admin_password}
                onChange={(e) => setRegisterForm({ ...registerForm, admin_password: e.target.value })}
              />
            </Field>
            <Button type="submit" disabled={isSubmitting} className="mt-2">
              {isSubmitting ? 'Creating…' : 'Create organization'}
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}
