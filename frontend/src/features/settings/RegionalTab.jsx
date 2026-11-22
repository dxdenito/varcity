import { useEffect, useMemo, useState } from 'react'
import { Globe, RotateCcw, Save } from 'lucide-react'

import { useAuth } from '../../auth/auth-context'
import Field from '../../components/ui/Field'
import SectionCard from '../../components/ui/SectionCard'
import { buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import { api } from '../../lib/api'
import { DATE_FORMATS, formatDate } from '../../lib/format'
import { useBranding } from '../../theme/branding-context'

const GENERAL_URL = '/api/v1/settings/general'

function listTimeZones(current) {
  const zones =
    typeof Intl.supportedValuesOf === 'function' ? Intl.supportedValuesOf('timeZone') : []
  return zones.includes(current) ? zones : [current, ...zones]
}

export default function RegionalTab() {
  const { user } = useAuth()
  const branding = useBranding()
  const canEdit = user.is_superuser

  const [saved, setSaved] = useState(null)
  const [form, setForm] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    api(GENERAL_URL)
      .then((data) => {
        setSaved(data)
        setForm(data)
      })
      .catch((err) => setLoadError(err.message))
  }, [])

  const timeZones = useMemo(() => (form ? listTimeZones(form.timezone) : []), [form])
  const dirty = Boolean(form && saved) && JSON.stringify(form) !== JSON.stringify(saved)

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!form) return <div aria-busy="true" />

  async function handleSave() {
    setMessage(null)
    setSaving(true)
    try {
      const result = await api(GENERAL_URL, { method: 'PUT', body: form })
      setSaved(result)
      setForm(result)
      await branding.refresh()
      setMessage({ type: 'success', text: 'Changes saved.' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <SectionCard
      icon={Globe}
      title="Regional settings"
      subtitle="Used for dates, reports and documents"
    >
      <fieldset disabled={!canEdit} className="min-w-0 space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Time zone" required>
            <select
              value={form.timezone}
              onChange={(event) => setForm({ ...form, timezone: event.target.value })}
              className={inputClass}
            >
              {timeZones.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Date format" required>
            <select
              value={form.date_format}
              onChange={(event) => setForm({ ...form, date_format: event.target.value })}
              className={inputClass}
            >
              {DATE_FORMATS.map((format) => (
                <option key={format} value={format}>
                  {format} ({formatDate(new Date(), format)})
                </option>
              ))}
            </select>
          </Field>
        </div>
      </fieldset>

      {message && (
        <p
          role={message.type === 'error' ? 'alert' : 'status'}
          className={`mt-4 rounded-lg p-3 text-sm ${
            message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
          }`}
        >
          {message.text}
        </p>
      )}

      {canEdit ? (
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => {
              setForm(saved)
              setMessage(null)
            }}
            disabled={!dirty || saving}
            className={buttonSecondary}
          >
            <RotateCcw size={16} aria-hidden="true" />
            Reset
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving}
            className={buttonPrimary}
          >
            <Save size={16} aria-hidden="true" />
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      ) : (
        <p className="mt-4 text-xs text-slate-500">You can view these settings but not change them.</p>
      )}
    </SectionCard>
  )
}