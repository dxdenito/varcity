import { useCallback, useMemo, useState } from 'react'
import { Lock } from 'lucide-react'

import { buttonPrimary, buttonSecondary, inputClass } from '../components/ui/styles'
import { ApiError, api } from '../lib/api'
import { ReauthContext } from './reauth-context'

export default function ReauthProvider({ children }) {
  const [pending, setPending] = useState(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const ask = useCallback(
    () =>
      new Promise((resolve, reject) => {
        setPassword('')
        setError(null)
        setPending({ resolve, reject })
      }),
    [],
  )

  const confirmed = useCallback(
    async (action) => {
      try {
        return await action()
      } catch (err) {
        if (err.status !== 428) throw err
        await ask()
        return action()
      }
    },
    [ask],
  )

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/api/v1/auth/reauth', { method: 'POST', body: { password } })
      pending.resolve()
      setPending(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function cancel() {
    pending.reject(new ApiError(428, 'Password confirmation was cancelled.'))
    setPending(null)
  }

  const value = useMemo(() => ({ confirmed }), [confirmed])

  return (
    <ReauthContext.Provider value={value}>
      {children}
      {pending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <form
            onSubmit={submit}
            role="dialog"
            aria-modal="true"
            aria-labelledby="reauth-title"
            className="w-full max-w-sm space-y-4 rounded-xl bg-white p-6 shadow-xl"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-700">
                <Lock size={18} aria-hidden="true" />
              </span>
              <div>
                <h2 id="reauth-title" className="text-base font-semibold text-slate-900">
                  Confirm your password
                </h2>
                <p className="text-xs text-slate-500">
                  This change needs a recent confirmation. You will not be asked again for 10
                  minutes.
                </p>
              </div>
            </div>

            <input
              type="password"
              required
              autoFocus
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-label="Password"
              className={inputClass}
            />

            {error && (
              <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button type="button" onClick={cancel} className={buttonSecondary}>
                Cancel
              </button>
              <button type="submit" disabled={busy || !password} className={buttonPrimary}>
                {busy ? 'Confirming...' : 'Confirm'}
              </button>
            </div>
          </form>
        </div>
      )}
    </ReauthContext.Provider>
  )
}