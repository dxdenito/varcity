import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../../lib/api'
import { useBranding } from '../../theme/branding-context'

export const PROFILE_URL = '/api/v1/settings/university'
const NULLABLE = new Set(['motto', 'address', 'website'])

const pick = (profile, keys) =>
  Object.fromEntries(keys.map((key) => [key, profile[key] ?? '']))

function toPatch(form) {
  const patch = {}
  for (const [key, value] of Object.entries(form)) {
    if (typeof value === 'string') {
      const trimmed = value.trim()
      patch[key] = NULLABLE.has(key) && !trimmed ? null : trimmed
    } else {
      patch[key] = value
    }
  }
  return patch
}

export function useProfileSection(keys) {
  const branding = useBranding()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    api(PROFILE_URL)
      .then((data) => {
        setProfile(data)
        setForm(pick(data, keys))
      })
      .catch((err) => setLoadError(err.message))
  }, [keys])

  const dirty = useMemo(
    () => Boolean(form && profile) && JSON.stringify(form) !== JSON.stringify(pick(profile, keys)),
    [form, profile, keys],
  )

  const setField = useCallback((key, value) => {
    setForm((current) => ({ ...current, [key]: value }))
  }, [])

  async function save() {
    setMessage(null)
    setSaving(true)
    try {
      const current = await api(PROFILE_URL)
      const base = { ...current }
      delete base.logo_url
      const saved = await api(PROFILE_URL, {
        method: 'PUT',
        body: { ...base, ...toPatch(form) },
      })
      setProfile(saved)
      setForm(pick(saved, keys))
      await branding.refresh()
      setMessage({ type: 'success', text: 'Changes saved.' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  function reset() {
    setForm(pick(profile, keys))
    setMessage(null)
  }

  async function reloadLogo() {
    const fresh = await api(PROFILE_URL)
    setProfile((current) => ({ ...current, logo_url: fresh.logo_url }))
    await branding.refresh()
  }

  return {
    profile,
    form,
    loadError,
    dirty,
    saving,
    message,
    setMessage,
    setField,
    save,
    reset,
    reloadLogo,
  }
}