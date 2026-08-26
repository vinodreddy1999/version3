import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { KeyRound } from 'lucide-react'
import { authApi } from '../api/endpoints'
import { Alert, Button, Field, Input } from '../components/ui'
import { errorMessage } from '../lib/apiClient'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDone, setIsDone] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setIsSubmitting(true)
    try {
      await authApi.resetPassword({ token, new_password: newPassword })
      setIsDone(true)
    } catch (err: unknown) {
      setError(errorMessage(err, 'This reset link is invalid or has expired.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-white to-indigo-50 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-200">
            <KeyRound className="h-6 w-6" strokeWidth={2} />
          </span>
          <h1 className="text-lg font-bold text-slate-900">Reset your password</h1>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50">
          {!token ? (
            <Alert>This reset link is missing its token. Request a new one from the sign-in page.</Alert>
          ) : isDone ? (
            <>
              <Alert tone="success">Your password has been updated.</Alert>
              <Link to="/login" className="mt-3 block text-center text-sm font-medium text-indigo-600 hover:text-indigo-700">
                Back to sign in
              </Link>
            </>
          ) : (
            <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
              {error && <Alert onDismiss={() => setError(null)}>{error}</Alert>}
              <Field label="New password">
                <Input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </Field>
              <Field label="Confirm new password">
                <Input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </Field>
              <Button type="submit" disabled={isSubmitting} className="mt-1 w-full">
                {isSubmitting ? 'Updating…' : 'Update password'}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
