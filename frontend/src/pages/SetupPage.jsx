import { useState } from 'react'

import { api } from '../lib/api'
import { readableTextColor } from '../lib/color'

const MIN_PASSWORD_LENGTH = 10 // the server enforces the real policy

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200'

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

export default function SetupPage() {
  const [form, setForm] = useState({
    setupCode: '',
    universityName: '',
    shortName: '',
    primaryColor: '#1d4ed8',
    sidebarColor: '#0f2557',
    adminEmail: '',
    adminPassword: '',
    confirmPassword: '',
  })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)

    if (form.adminPassword.length < MIN_PASSWORD_LENGTH) {
      setError(`The password must be at least ${MIN_PASSWORD_LENGTH} characters long.`)
      return
    }
    if (form.adminPassword !== form.confirmPassword) {
      setError('The two passwords do not match.')
      return
    }

    setBusy(true)
    try {
      await api('/api/v1/setup/complete', {
        method: 'POST',
        body: {
          setup_code: form.setupCode,
          university_name: form.universityName,
          short_name: form.shortName,
          primary_color: form.primaryColor,
          sidebar_color: form.sidebarColor,
          admin_email: form.adminEmail,
          admin_password: form.adminPassword,
        },
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 p-6">
        <div className="w-full max-w-md rounded-xl bg-white p-8 text-center shadow">
          <h1 className="text-xl font-semibold text-slate-900">Setup complete</h1>
          <p className="mt-2 text-sm text-slate-600">
            Your institution is configured. Sign in with the administrator account you just created.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-on-brand hover:bg-brand-700"
          >
            Go to sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen justify-center bg-slate-100 p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-lg space-y-8 py-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Welcome to Varcity</h1>
          <p className="mt-1 text-sm text-slate-600">
            Set up your institution. This screen appears only once, on a new installation.
          </p>
        </header>

        <section className="space-y-4 rounded-xl bg-white p-6 shadow-sm">
          <h2 className="font-medium text-slate-900">1. Verify the installation</h2>
          <Field
            label="Setup code"
            hint="Shown in the server console where Varcity was started."
          >
            <input
              required
              autoComplete="off"
              value={form.setupCode}
              onChange={update('setupCode')}
              placeholder="ABCD-EFGH-IJKL"
              className={`${inputClass} font-mono uppercase`}
            />
          </Field>
        </section>

        <section className="space-y-4 rounded-xl bg-white p-6 shadow-sm">
          <h2 className="font-medium text-slate-900">2. Your university</h2>
          <Field label="University name">
            <input
              required
              maxLength={120}
              value={form.universityName}
              onChange={update('universityName')}
              className={inputClass}
            />
          </Field>
          <Field label="Short name" hint="Shown in the menu header, for example KU.">
            <input
              required
              maxLength={40}
              value={form.shortName}
              onChange={update('shortName')}
              className={inputClass}
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Primary colour">
              <input
                type="color"
                value={form.primaryColor}
                onChange={update('primaryColor')}
                className="mt-1 h-10 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
              />
            </Field>
            <Field label="Menu colour">
              <input
                type="color"
                value={form.sidebarColor}
                onChange={update('sidebarColor')}
                className="mt-1 h-10 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
              />
            </Field>
          </div>

          <div className="flex overflow-hidden rounded-lg border border-slate-200" aria-hidden="true">
            <div
              className="w-1/3 p-3 text-xs font-medium"
              style={{
                backgroundColor: form.sidebarColor,
                color: readableTextColor(form.sidebarColor),
              }}
            >
              {form.shortName || 'Short name'}
            </div>
            <div className="flex flex-1 items-center justify-center bg-slate-50 p-3">
              <span
                className="rounded-lg px-3 py-1.5 text-xs font-medium"
                style={{
                  backgroundColor: form.primaryColor,
                  color: readableTextColor(form.primaryColor),
                }}
              >
                Preview
              </span>
            </div>
          </div>
          <p className="text-xs text-slate-500">
            You can add a logo and change these later in Settings.
          </p>
        </section>

        <section className="space-y-4 rounded-xl bg-white p-6 shadow-sm">
          <h2 className="font-medium text-slate-900">3. System administrator</h2>
          <Field label="Email">
            <input
              type="email"
              required
              autoComplete="off"
              value={form.adminEmail}
              onChange={update('adminEmail')}
              className={inputClass}
            />
          </Field>
          <Field label="Password" hint={`At least ${MIN_PASSWORD_LENGTH} characters.`}>
            <input
              type="password"
              required
              autoComplete="new-password"
              value={form.adminPassword}
              onChange={update('adminPassword')}
              className={inputClass}
            />
          </Field>
          <Field label="Confirm password">
            <input
              type="password"
              required
              autoComplete="new-password"
              value={form.confirmPassword}
              onChange={update('confirmPassword')}
              className={inputClass}
            />
          </Field>
        </section>

        {error && (
          <p role="alert" className="rounded bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-medium text-on-brand hover:bg-brand-700 disabled:opacity-60"
        >
          {busy ? 'Setting up...' : 'Complete setup'}
        </button>
      </form>
    </div>
  )
}