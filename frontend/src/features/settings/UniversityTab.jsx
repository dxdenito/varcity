import { useRef } from 'react'
import { Landmark, Trash2, Upload } from 'lucide-react'

import { usePermissions } from '../../auth/usePermissions'
import BrandLogo from '../../components/BrandLogo'
import Field from '../../components/ui/Field'
import FormActions from '../../components/ui/FormActions'
import SectionCard from '../../components/ui/SectionCard'
import { buttonDanger, buttonSecondary, inputClass } from '../../components/ui/styles'
import { api } from '../../lib/api'
import { PROFILE_URL, useProfileSection } from './useProfileSection'
import { SETTINGS } from './settings-permissions'

const KEYS = ['university_name', 'short_name', 'motto', 'address', 'website']
const LOGO_URL = `${PROFILE_URL}/logo`

export default function UniversityTab() {
  const { can } = usePermissions()
  const canEdit = can(SETTINGS.universityUpdate)
  const fileInput = useRef(null)
  const section = useProfileSection(KEYS)
  const { profile, form, loadError, setField, setMessage, reloadLogo } = section

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!form) return <div aria-busy="true" />

  const set = (key) => (event) => setField(key, event.target.value)

  async function changeLogo(action) {
    setMessage(null)
    try {
      await action()
      await reloadLogo()
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
    <div className="space-y-4">
      <fieldset disabled={!canEdit} className="min-w-0">
        <SectionCard
          icon={Landmark}
          title="University information"
          subtitle="Shown on the login page, documents and emails"
        >
          <div className="flex flex-col gap-6 sm:flex-row">
            <div className="flex shrink-0 flex-col items-center gap-3 sm:w-40">
              <div className="flex h-28 w-28 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 p-2">
                <BrandLogo
                  branding={{ logo_url: profile.logo_url, short_name: form.short_name || '?' }}
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
                  value={form.university_name}
                  onChange={set('university_name')}
                  className={inputClass}
                />
              </Field>
              <Field label="Short name" required hint="Shown in the menu, for example KU.">
                <input
                  required
                  maxLength={40}
                  value={form.short_name}
                  onChange={set('short_name')}
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
      </fieldset>

      <FormActions
        canEdit={canEdit}
        dirty={section.dirty}
        saving={section.saving}
        message={section.message}
        onSave={section.save}
        onReset={section.reset}
      />
    </div>
  )
}