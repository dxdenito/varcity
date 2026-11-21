import { useEffect, useState } from 'react'

import { useAuth } from './auth/auth-context'
import AuthProvider from './auth/AuthProvider'
import AppShell from './components/layout/AppShell'
import { api } from './lib/api'
import LoginPage from './pages/LoginPage'
import SetupPage from './pages/SetupPage'
import BrandingProvider from './theme/BrandingProvider'
import { useBranding } from './theme/branding-context'

const SHADES = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']

function BlankScreen() {
  return <div className="min-h-screen bg-slate-100" aria-busy="true" />
}

function DashboardPlaceholder() {
  const branding = useBranding()

  return (
    <div className="space-y-6">
      <section className="rounded-xl bg-gradient-to-r from-brand-950 to-brand-700 p-8 text-white">
        <h1 className="text-2xl font-semibold sm:text-3xl">Welcome to {branding.short_name}</h1>
        <p className="mt-2 text-sm opacity-90">{branding.university_name}</p>
      </section>

      {/* Temporary: shows the palette generated from the primary colour. */}
      <section className="rounded-xl bg-white p-6 shadow-sm">
        <h2 className="text-sm font-medium text-slate-700">Theme preview</h2>
        <div className="mt-3 flex overflow-hidden rounded-lg">
          {SHADES.map((shade) => (
            <div
              key={shade}
              className="flex h-16 flex-1 items-end justify-center pb-1 text-[10px] text-slate-700"
              style={{ backgroundColor: `var(--brand-${shade})` }}
            >
              {shade}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

// Signed in -> the application. Otherwise -> the login screen.
function AuthenticatedApp() {
  const { status } = useAuth()

  if (status === 'loading') return <BlankScreen />
  if (status === 'anonymous') return <LoginPage />

  return (
    <AppShell>
      <DashboardPlaceholder />
    </AppShell>
  )
}

// First decide whether this installation still needs its one-time setup.
function Gate() {
  const [setupRequired, setSetupRequired] = useState(null) // null = still checking

  useEffect(() => {
    api('/api/v1/setup/status')
      .then((data) => setSetupRequired(data.setup_required))
      .catch(() => setSetupRequired(false)) // server unreachable: the login page will say so
  }, [])

  if (setupRequired === null) return <BlankScreen />
  if (setupRequired) return <SetupPage />

  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  )
}

export default function App() {
  return (
    <BrandingProvider>
      <Gate />
    </BrandingProvider>
  )
}