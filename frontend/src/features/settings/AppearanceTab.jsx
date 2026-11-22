import { Palette } from 'lucide-react'

import { useAuth } from '../../auth/auth-context'
import ColourPreview from '../../components/ColourPreview'
import Field from '../../components/ui/Field'
import FormActions from '../../components/ui/FormActions'
import SectionCard from '../../components/ui/SectionCard'
import Toggle from '../../components/ui/Toggle'
import { useProfileSection } from './useProfileSection'

const KEYS = ['primary_color', 'sidebar_color', 'show_powered_by']

export default function AppearanceTab() {
  const { user } = useAuth()
  const canEdit = user.is_superuser
  const section = useProfileSection(KEYS)
  const { profile, form, loadError, setField } = section

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!form) return <div aria-busy="true" />

  return (
    <div className="space-y-4">
      <fieldset disabled={!canEdit} className="min-w-0">
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
                    value={form.primary_color}
                    onChange={(event) => setField('primary_color', event.target.value)}
                    className="mt-1 h-10 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1"
                  />
                </Field>
                <Field label="Menu colour">
                  <input
                    type="color"
                    value={form.sidebar_color}
                    onChange={(event) => setField('sidebar_color', event.target.value)}
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
                  checked={form.show_powered_by}
                  onChange={(value) => setField('show_powered_by', value)}
                  label="Show Powered by Varcity"
                />
              </div>
            </div>
            <ColourPreview
              primary={form.primary_color}
              sidebar={form.sidebar_color}
              label={profile.short_name}
            />
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