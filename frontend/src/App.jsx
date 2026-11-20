import AppShell from './components/layout/AppShell'
import BrandingProvider from './theme/BrandingProvider'
import { useBranding } from './theme/branding-context'

const SHADES = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']

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
        <button
          type="button"
          className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-on-brand hover:bg-brand-700"
        >
          Primary button
        </button>
      </section>
    </div>
  )
}

export default function App() {
  return (
    <BrandingProvider>
      <AppShell>
        <DashboardPlaceholder />
      </AppShell>
    </BrandingProvider>
  )
}