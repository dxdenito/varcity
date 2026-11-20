import { createContext, useContext } from 'react'

// Used if the branding cannot be loaded from the server.
export const FALLBACK_BRANDING = {
  university_name: 'Varcity',
  short_name: 'Varcity',
  logo_url: null,
  show_powered_by: true,
}

export const BrandingContext = createContext(FALLBACK_BRANDING)

export function useBranding() {
  return useContext(BrandingContext)
}