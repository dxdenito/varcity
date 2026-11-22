import { useState } from 'react'

import { useAuth } from '../auth/auth-context'
import BrandBackdrop from '../components/BrandBackdrop'
import BrandLogo from '../components/BrandLogo'
import { useBranding } from '../theme/branding-context'

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200'

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
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <BrandBackdrop>
      <div className="grid min-h-screen grid-rows-[auto_1fr] lg:grid-cols-2 lg:grid-rows-1">
        <section className="flex flex-col justify-between p-6 lg:p-12">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-white/90 p-1 shadow-lg">
              <BrandLogo branding={branding} size="h-14 w-14" />
            </div>
            <span className="text-lg font-semibold">{branding.short_name}</span>
          </div>

          <div className="hidden max-w-md lg:block">
            <h1 className="text-4xl font-semibold leading-tight">
              Welcome to {branding.university_name}
            </h1>
            <p className="mt-4 text-lg opacity-80">
              {branding.motto || 'One account for every university system.'}
            </p>
          </div>

          <p className="hidden text-sm opacity-60 lg:block">
            {branding.show_powered_by ? 'Powered by Varcity' : ''}
          </p>
        </section>

        <section className="flex flex-col items-center justify-center p-4 sm:p-8">
          <div className="w-full max-w-sm rounded-2xl bg-white p-8 text-slate-900 shadow-2xl">
            <h2 className="text-2xl font-semibold">Sign in</h2>
            <p className="mt-1 text-sm text-slate-500">Use your institutional account.</p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">Email</span>
                <input
                  type="email"
                  required
                  autoFocus
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
                <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-medium text-on-brand hover:bg-brand-700 disabled:opacity-60"
              >
                {busy ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          </div>

          {branding.show_powered_by && (
            <p className="mt-6 text-xs opacity-70 lg:hidden">Powered by Varcity</p>
          )}
        </section>
      </div>
    </BrandBackdrop>
  )
}