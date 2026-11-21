import { useState } from 'react'

import { useAuth } from '../auth/auth-context'
import BrandLogo from '../components/BrandLogo'
import { useBranding } from '../theme/branding-context'

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200'

export default function LoginPage() {
  const branding = useBranding()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await login(email, password)
      // On success this page is replaced by the application.
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-100 p-6">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow">
        <div className="flex flex-col items-center text-center">
          <BrandLogo branding={branding} />
          <h1 className="mt-4 text-xl font-semibold text-slate-900">{branding.university_name}</h1>
          <p className="mt-1 text-sm text-slate-500">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email</span>
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={inputClass}
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={inputClass}
            />
          </label>

          {error && (
            <p role="alert" className="rounded bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-on-brand hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>

      {branding.show_powered_by && (
        <p className="mt-6 text-xs text-slate-500">Powered by Varcity</p>
      )}
    </div>
  )
}