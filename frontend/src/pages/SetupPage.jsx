import { useState } from 'react'
import { Check, GraduationCap, Server, ShieldCheck } from 'lucide-react'

import VarcityLogo from '../components/VarcityLogo'
import { api } from '../lib/api'
import { readableTextColor } from '../lib/color'

const MIN_PASSWORD_LENGTH = 10
const STEPS = ['Verify', 'University', 'Administrator']

const HIGHLIGHTS = [
  {
    icon: Server,
    title: 'Runs on your own servers',
    text: 'Your data and configuration stay with your institution.',
  },
  {
    icon: ShieldCheck,
    title: 'One secure identity',
    text: 'Staff and students sign in once, everywhere.',
  },
  {
    icon: GraduationCap,
    title: 'Made for your university',
    text: 'Structure, names and colours are yours to configure.',
  },
]

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100'

function Backdrop({ children }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div className="pointer-events-none absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-blue-600/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-48 right-0 h-[36rem] w-[36rem] rounded-full bg-indigo-500/25 blur-3xl" />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />
      <div className="relative">{children}</div>
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

function Stepper({ step }) {
  return (
    <ol className="flex items-center" aria-label="Setup progress">
      {STEPS.map((label, index) => (
        <li key={label} className="flex flex-1 items-center last:flex-none">
          <div className="flex items-center gap-2" aria-current={index === step ? 'step' : undefined}>
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                index < step
                  ? 'bg-blue-600 text-white'
                  : index === step
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                    : 'bg-slate-100 text-slate-400'
              }`}
            >
              {index < step ? <Check size={16} aria-hidden="true" /> : index + 1}
            </span>
            <span
              className={`hidden text-sm sm:inline ${
                index === step ? 'font-medium text-slate-900' : 'text-slate-500'
              }`}
            >
              {label}
            </span>
          </div>
          {index < STEPS.length - 1 && (
            <span className={`mx-3 h-px flex-1 ${index < step ? 'bg-blue-600' : 'bg-slate-200'}`} />
          )}
        </li>
      ))}
    </ol>
  )
}

function ColourPreview({ form }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200" aria-hidden="true">
      <div className="flex h-28">
        <div
          className="flex w-1/3 flex-col gap-2 p-3 text-xs"
          style={{
            backgroundColor: form.sidebarColor,
            color: readableTextColor(form.sidebarColor),
          }}
        >
          <span className="truncate font-semibold">{form.shortName || 'Short name'}</span>
          <span className="h-2 w-3/4 rounded bg-current opacity-30" />
          <span className="h-2 w-1/2 rounded bg-current opacity-30" />
        </div>
        <div className="flex flex-1 flex-col items-start justify-center gap-2 bg-slate-50 p-4">
          <span className="h-2 w-24 rounded bg-slate-300" />
          <span
            className="rounded-md px-3 py-1.5 text-xs font-medium"
            style={{
              backgroundColor: form.primaryColor,
              color: readableTextColor(form.primaryColor),
            }}
          >
            Primary button
          </span>
        </div>
      </div>
    </div>
  )
}

export default function SetupPage() {
  const [form, setForm] = useState({
    setupCode: '',
    universityName: '',
    shortName: '',
    primaryColor: '#1d4ed8',
    sidebarColor: '#0f2557',
    adminFullName: '',
    adminEmail: '',
    adminPassword: '',
    confirmPassword: '',
  })
  const [step, setStep] = useState(0)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value })
  const isLastStep = step === STEPS.length - 1

  function validate() {
    if (step === 0 && !form.setupCode.trim()) {
      return 'Enter the setup code shown in the server console.'
    }
    if (step === 1 && (!form.universityName.trim() || !form.shortName.trim())) {
      return 'Enter the university name and a short name.'
    }
    if (step === 2) {
      if (!form.adminFullName.trim()) return 'Enter the administrator’s full name.'
      if (form.adminPassword.length < MIN_PASSWORD_LENGTH) {
        return `The password must be at least ${MIN_PASSWORD_LENGTH} characters long.`
      }
      if (form.adminPassword !== form.confirmPassword) return 'The two passwords do not match.'
    }
    return null
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const problem = validate()
    if (problem) {
      setError(problem)
      return
    }
    setError(null)

    if (!isLastStep) {
      setStep(step + 1)
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
          admin_full_name: form.adminFullName,
          admin_email: form.adminEmail,
          admin_password: form.adminPassword,
        },
      })
      setDone(true)
    } catch (err) {
      setError(err.message)
      if (err.status === 403) setStep(0)
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <Backdrop>
        <div className="flex min-h-screen items-center justify-center p-6">
          <div className="w-full max-w-md rounded-2xl bg-white p-10 text-center text-slate-900 shadow-2xl">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-green-600">
              <Check size={28} aria-hidden="true" />
            </span>
            <h1 className="mt-5 text-2xl font-semibold">Setup complete</h1>
            <p className="mt-2 text-sm text-slate-600">
              Your institution is configured. Sign in with the administrator account you just
              created.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-8 w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              Go to sign in
            </button>
          </div>
        </div>
      </Backdrop>
    )
  }

  return (
    <Backdrop>
      <div className="grid min-h-screen lg:grid-cols-2">
        <section className="hidden flex-col justify-between p-12 lg:flex">
          <VarcityLogo size={44} />
          <div className="max-w-md">
            <h1 className="text-4xl font-semibold leading-tight">Set up your university</h1>
            <p className="mt-4 text-lg text-slate-300">
              Institutional identity, academics and administration in one platform you control.
            </p>
            <ul className="mt-10 space-y-6">
              {HIGHLIGHTS.map(({ icon: Icon, title, text }) => (
                <li key={title} className="flex gap-4">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/10 text-blue-300">
                    <Icon size={20} aria-hidden="true" />
                  </span>
                  <div>
                    <p className="font-medium">{title}</p>
                    <p className="text-sm text-slate-400">{text}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <p className="text-sm text-slate-500">Varcity University ERP</p>
        </section>

        <section className="flex items-center justify-center p-4 sm:p-8">
          <div className="w-full max-w-lg">
            <div className="mb-6 lg:hidden">
              <VarcityLogo />
            </div>

            <form
              onSubmit={handleSubmit}
              className="rounded-2xl bg-white p-6 text-slate-900 shadow-2xl sm:p-8"
            >
              <Stepper step={step} />

              <div className="mt-8 space-y-5">
                {step === 0 && (
                  <>
                    <div>
                      <h2 className="text-xl font-semibold">Verify this installation</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Enter the setup code printed in the console where Varcity was started.
                      </p>
                    </div>
                    <Field label="Setup code">
                      <input
                        autoFocus
                        autoComplete="off"
                        value={form.setupCode}
                        onChange={update('setupCode')}
                        placeholder="ABCD-EFGH-IJKL"
                        className={`${inputClass} font-mono uppercase tracking-wider`}
                      />
                    </Field>
                  </>
                )}

                {step === 1 && (
                  <>
                    <div>
                      <h2 className="text-xl font-semibold">Your university</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        This is how Varcity looks to your staff and students.
                      </p>
                    </div>
                    <Field label="University name">
                      <input
                        maxLength={120}
                        value={form.universityName}
                        onChange={update('universityName')}
                        className={inputClass}
                      />
                    </Field>
                    <Field label="Short name" hint="Shown in the menu header, for example KU.">
                      <input
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
                          className="mt-1 h-11 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
                        />
                      </Field>
                      <Field label="Menu colour">
                        <input
                          type="color"
                          value={form.sidebarColor}
                          onChange={update('sidebarColor')}
                          className="mt-1 h-11 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
                        />
                      </Field>
                    </div>
                    <ColourPreview form={form} />
                    <p className="text-xs text-slate-500">
                      You can add a logo and change these later in Settings.
                    </p>
                  </>
                )}

                {step === 2 && (
                  <>
                    <div>
                      <h2 className="text-xl font-semibold">System administrator</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        The first account, with full access. Every other user is created from the
                        staff and student directory.
                      </p>
                    </div>
                    <Field label="Full name">
                      <input
                        maxLength={200}
                        autoComplete="off"
                        value={form.adminFullName}
                        onChange={update('adminFullName')}
                        className={inputClass}
                      />
                    </Field>
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
                        autoComplete="new-password"
                        value={form.adminPassword}
                        onChange={update('adminPassword')}
                        className={inputClass}
                      />
                    </Field>
                    <Field label="Confirm password">
                      <input
                        type="password"
                        autoComplete="new-password"
                        value={form.confirmPassword}
                        onChange={update('confirmPassword')}
                        className={inputClass}
                      />
                    </Field>
                  </>
                )}
              </div>

              {error && (
                <p role="alert" className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                  {error}
                </p>
              )}

              <div className="mt-8 flex gap-3">
                {step > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setError(null)
                      setStep(step - 1)
                    }}
                    className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Back
                  </button>
                )}
                <button
                  type="submit"
                  disabled={busy}
                  className="flex-1 rounded-lg bg-blue-600 px-5 py-3 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                >
                  {busy ? 'Setting up...' : isLastStep ? 'Complete setup' : 'Continue'}
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </Backdrop>
  )
}