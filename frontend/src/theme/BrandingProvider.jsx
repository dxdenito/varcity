import { useEffect, useState } from 'react'

import { BrandingContext, FALLBACK_BRANDING } from './branding-context'

const SHADES = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950']

// Write the server's colours into CSS variables on the page.
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

  useEffect(() => {
    let cancelled = false

    fetch('/api/v1/public/branding')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (cancelled) return
        applyColors(data.colors)
        document.title = data.university_name
        setBranding(data)
      })
      .catch(() => {
        if (cancelled) return
        document.title = FALLBACK_BRANDING.university_name
        setBranding(FALLBACK_BRANDING)
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Show an empty page (not the wrong colours) while branding loads.
  if (!branding) {
    return <div className="min-h-screen bg-slate-100" aria-busy="true" />
  }

  return <BrandingContext.Provider value={branding}>{children}</BrandingContext.Provider>
}