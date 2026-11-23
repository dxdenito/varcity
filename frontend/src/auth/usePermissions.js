import { useMemo } from 'react'

import { useAuth } from './auth-context'

export function usePermissions() {
  const { permissions } = useAuth()

  return useMemo(() => {
    const all = Boolean(permissions?.all)
    const everywhere = new Set(permissions?.everywhere ?? [])
    const scoped = permissions?.scoped ?? {}

    const can = (code) => all || everywhere.has(code)
    const canAnywhere = (code) => can(code) || (scoped[code]?.length ?? 0) > 0
    const canAt = (code, chain) =>
      can(code) || (scoped[code] ?? []).some((id) => chain.includes(id))

    return { can, canAnywhere, canAt, holdsAll: all }
  }, [permissions])
}