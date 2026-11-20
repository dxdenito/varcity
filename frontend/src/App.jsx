import { useEffect, useState } from 'react'

export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/v1/health/live')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-semibold text-slate-900">Varcity</h1>
        <p className="mt-1 text-sm text-slate-500">University ERP</p>

        <div className="mt-6 border-t border-slate-200 pt-6">
          <h2 className="text-sm font-medium text-slate-700">Backend status</h2>

          {error && (
            <p className="mt-2 rounded bg-red-50 p-3 text-sm text-red-700">
              Cannot reach the backend: {error}
            </p>
          )}

          {!error && !health && (
            <p className="mt-2 text-sm text-slate-500">Checking...</p>
          )}

          {health && (
            <dl className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Status</dt>
                <dd className="font-medium text-green-600">{health.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Version</dt>
                <dd>{health.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Environment</dt>
                <dd>{health.environment}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  )
}