import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../lib/api'
import { BrandingContext, FALLBACK_BRANDING } from './branding-context'

const SHADES = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']

function applyColors(colors) {
  const root = document.documentElement
  for (const shade of SHADES) {
    root.style.setProperty(`--brand-${shade}`, colors.primary[shade])
  }
  root.style.setProperty('--on-primary', colors.on_primary)
  root.style.setProperty('--sidebar', colors.sidebar)
  root.style.setProperty('--on-sidebar', colors.on_sidebar)
}

export default function BrandingProvider({ children }) {
  const [branding, setBranding] = useState(null)

  const load = useCallback(async (fresh = false) => {
    try {
      const data = await api('/api/v1/public/branding', { cache: fresh ? 'reload' : undefined })
      applyColors(data.colors)
      document.title = data.university_name
      setBranding(data)
    } catch {
      setBranding((current) => current ?? FALLBACK_BRANDING)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const value = useMemo(
    () => (branding ? { ...branding, refresh: () => load(true) } : null),
    [branding, load],
  )

  if (!value) return <div className="min-h-screen bg-slate-100" aria-busy="true" />

  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>
}