import { Navigate, NavLink, Outlet } from 'react-router-dom'
import { SlidersHorizontal } from 'lucide-react'

import { usePermissions } from '../../auth/usePermissions'
import PageHeader from '../../components/ui/PageHeader'
import { SETTINGS } from './settings-permissions'

const TABS = [
  { label: 'University', to: 'university', perm: SETTINGS.universityView },
  { label: 'Appearance', to: 'appearance', perm: SETTINGS.universityView },
  { label: 'Regional', to: 'regional', perm: SETTINGS.generalView },
]

function useVisibleTabs() {
  const { canAnywhere } = usePermissions()
  return TABS.filter((tab) => canAnywhere(tab.perm))
}

export function FirstTabRedirect() {
  const tabs = useVisibleTabs()
  return tabs.length ? <Navigate to={tabs[0].to} replace /> : null
}

export default function GeneralSettingsPage() {
  const tabs = useVisibleTabs()

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <PageHeader
        icon={SlidersHorizontal}
        title="General settings"
        subtitle="System-wide preferences for the whole installation"
      />

      <nav aria-label="General settings sections" className="flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `-mb-px border-b-2 px-4 py-2 text-sm ${
                isActive
                  ? 'border-brand-600 font-medium text-brand-700'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  )
}