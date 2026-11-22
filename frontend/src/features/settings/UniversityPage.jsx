import { useEffect, useMemo, useRef, useState } from 'react'
import { Landmark, Palette, RotateCcw, Save, Trash2, Upload } from 'lucide-react'

import { useAuth } from '../../auth/auth-context'
import BrandLogo from '../../components/BrandLogo'
import ColourPreview from '../../components/ColourPreview'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import SectionCard from '../../components/ui/SectionCard'
import { buttonDanger, buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import Toggle from '../../components/ui/Toggle'
import { api } from '../../lib/api'
import { useBranding } from '../../theme/branding-context'

const PROFILE_URL = '/api/v1/settings/university'
const LOGO_URL = `${PROFILE_URL}/logo`

const toForm = (profile) => ({
  universityName: profile.university_name,
  shortName: profile.short_name,
  motto: profile.motto ?? '',
  address: profile.address ?? '',
  website: profile.website ?? '',
  primaryColor: profile.primary_color,
  sidebarColor: profile.sidebar_color,
  showPoweredBy: profile.show_powered_by,
})

const toPayload = (form) => ({
  university_name: form.universityName.trim(),
  short_name: form.shortName.trim(),
  motto: form.motto.trim() || null,
  address: form.address.trim() || null,
  website: form.website.trim() || null,
  primary_color: form.primaryColor,
  sidebar_color: form.sidebarColor,
  show_powered_by: form.showPoweredBy,
})

export default function UniversityPage() {
  const { user } = useAuth()
  const branding = useBranding()
  const canEdit = user.is_superuser
  const fileInput = useRef(null)

  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    api(PROFILE_URL)
      .then((data) => {
        setProfile(data)
        setForm(toForm(data))
      })
      .catch((err) => setLoadError(err.message))
  }, [])

  const dirty = useMemo(
    () => Boolean(form && profile) && JSON.stringify(form) !== JSON.stringify(toForm(profile)),
    [form, profile],
  )

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!form) return <div aria-busy="true" />

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  async function handleSave() {
    setMessage(null)
    setSaving(true)
    try {
      const saved = await api(PROFILE_URL, { method: 'PUT', body: toPayload(form) })
      setProfile(saved)
      setForm(toForm(saved))
      await branding.refresh()
      setMessage({ type: 'success', text: 'Changes saved.' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  function handleReset() {
    setForm(toForm(profile))
    setMessage(null)
  }

  async function changeLogo(action) {
    setMessage(null)
    try {
      await action()
      const fresh = await api(PROFILE_URL)
      setProfile((current) => ({ ...current, logo_url: fresh.logo_url }))
      await branding.refresh()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  function handleLogoPicked(event) {
    const file = event.target.files[0]
    event.target.value = ''
    if (!file) return
    const body = new FormData()
    body.append('file', file)
    changeLogo(() => api(LOGO_URL, { method: 'POST', body }))
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader
        icon={Landmark}
        title="University"
        subtitle="Your institution's details and appearance"
        actions={
          canEdit && (
            <>
              <button
                type="button"
                onClick={handleReset}
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
            </>
          )
        }
      />

      {message && (
        <p
          role={message.type === 'error' ? 'alert' : 'status'}
          className={`rounded-lg p-3 text-sm ${
            message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
          }`}
        >
          {message.text}
        </p>
      )}
      {!canEdit && (
        <p className="text-xs text-slate-500">You can view these settings but not change them.</p>
      )}
      {canEdit && dirty && <p className="text-xs text-amber-700">You have unsaved changes.</p>}

      <fieldset disabled={!canEdit} className="min-w-0 space-y-5">
        <SectionCard
          icon={Landmark}
          title="University information"
          subtitle="Shown on the login page, documents and emails"
        >
          <div className="flex flex-col gap-6 sm:flex-row">
            <div className="flex shrink-0 flex-col items-center gap-3 sm:w-40">
              <div className="flex h-28 w-28 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 p-2">
                <BrandLogo
                  branding={{ logo_url: profile.logo_url, short_name: form.shortName || '?' }}
                  size="h-24 w-24"
                />
              </div>
              <input
                ref={fileInput}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleLogoPicked}
                className="hidden"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => fileInput.current.click()}
                  className={buttonSecondary}
                >
                  <Upload size={16} aria-hidden="true" />
                  {profile.logo_url ? 'Replace' : 'Upload logo'}
                </button>
                {profile.logo_url && (
                  <button
                    type="button"
                    onClick={() => changeLogo(() => api(LOGO_URL, { method: 'DELETE' }))}
                    aria-label="Remove logo"
                    className={buttonDanger}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                )}
              </div>
              <p className="text-center text-xs text-slate-500">PNG, JPEG or WebP, up to 512 KB</p>
            </div>

            <div className="grid flex-1 gap-4 sm:grid-cols-2">
              <Field label="University name" required>
                <input
                  required
                  maxLength={120}
                  value={form.universityName}
                  onChange={set('universityName')}
                  className={inputClass}
                />
              </Field>
              <Field label="Short name" required hint="Shown in the menu, for example KU.">
                <input
                  required
                  maxLength={40}
                  value={form.shortName}
                  onChange={set('shortName')}
                  className={inputClass}
                />
              </Field>
              <Field label="Motto" className="sm:col-span-2">
                <input
                  maxLength={200}
                  value={form.motto}
                  onChange={set('motto')}
                  className={inputClass}
                />
              </Field>
              <Field label="Website">
                <input
                  type="url"
                  maxLength={200}
                  placeholder="https://"
                  value={form.website}
                  onChange={set('website')}
                  className={inputClass}
                />
              </Field>
              <Field label="Address">
                <textarea
                  rows={2}
                  maxLength={500}
                  value={form.address}
                  onChange={set('address')}
                  className={inputClass}
                />
              </Field>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          icon={Palette}
          title="Appearance"
          subtitle="Colours used across the application"
        >
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Primary colour">
                  <input
                    type="color"
                    value={form.primaryColor}
                    onChange={set('primaryColor')}
                    className="mt-1 h-10 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
                  />
                </Field>
                <Field label="Menu colour">
                  <input
                    type="color"
                    value={form.sidebarColor}
                    onChange={set('sidebarColor')}
                    className="mt-1 h-10 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
                  />
                </Field>
              </div>
              <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 p-3">
                <div>
                  <p className="text-sm font-medium text-slate-800">Show “Powered by Varcity”</p>
                  <p className="text-xs text-slate-500">In the footer and on the login page.</p>
                </div>
                <Toggle
                  checked={form.showPoweredBy}
                  onChange={(value) => setForm({ ...form, showPoweredBy: value })}
                  label="Show Powered by Varcity"
                />
              </div>
            </div>
            <ColourPreview
              primary={form.primaryColor}
              sidebar={form.sidebarColor}
              label={form.shortName}
            />
          </div>
        </SectionCard>
      </fieldset>
    </div>
  )
}