import { createContext, useContext } from 'react'

export const FALLBACK_BRANDING = {
  university_name: 'Varcity',
  short_name: 'Varcity',
  motto: null,
  logo_url: null,
  show_powered_by: true,
  timezone: 'Africa/Nairobi',
  date_format: 'DD/MM/YYYY',
  refresh: async () => {},
}

export const BrandingContext = createContext(FALLBACK_BRANDING)

export function useBranding() {
  return useContext(BrandingContext)
}