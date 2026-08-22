import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Factory } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Alert, Button, Field, Input } from '../components/ui'

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

  const switchMode = (next: 'login' | 'register') => {
    setMode(next)
    setError(null)
  }

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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-indigo-50 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-200">
            <Factory className="h-6 w-6" strokeWidth={2} />
          </span>
          <h1 className="text-lg font-bold text-slate-900">Metam ERP</h1>
          <p className="text-sm text-slate-500">Manufacturing operations, run for real.</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50">
          <div className="mb-5 flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
            <button
              className={`flex-1 rounded-md py-1.5 font-medium transition-colors ${
                mode === 'login' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => switchMode('login')}
            >
              Sign in
            </button>
            <button
              className={`flex-1 rounded-md py-1.5 font-medium transition-colors ${
                mode === 'register' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => switchMode('register')}
            >
              New organization
            </button>
          </div>

          {error && <Alert onDismiss={() => setError(null)}>{error}</Alert>}

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
              <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
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
              <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
                {isSubmitting ? 'Creating…' : 'Create organization'}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
