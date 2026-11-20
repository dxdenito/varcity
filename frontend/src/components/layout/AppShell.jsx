import { useState } from 'react'
import {
  Bell,
  BookOpen,
  Briefcase,
  Building2,
  ClipboardList,
  Contact,
  FileCheck,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  TrendingUp,
  User,
  Users,
  Wallet,
  Workflow,
  X,
} from 'lucide-react'

import { useBranding } from '../../theme/branding-context'

// Placeholder menu copied from the design mockup. It will later be built
// from the enabled modules and the signed-in user's permissions.
const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, active: true },
  { label: 'Institutional Directory', icon: Contact },
  { label: 'Academic Management', icon: GraduationCap },
  { label: 'Admissions', icon: ClipboardList },
  { label: 'Student Management', icon: Users },
  { label: 'Staff Management', icon: Briefcase },
  { label: 'Finance', icon: Wallet },
  { label: 'Examinations', icon: FileCheck },
  { label: 'Library', icon: BookOpen },
  { label: 'Hostel Management', icon: Building2 },
  { label: 'Workflow', icon: Workflow },
  { label: 'Reports & Analytics', icon: TrendingUp },
  { label: 'Settings', icon: Settings },
  { label: 'System Administration', icon: ShieldCheck },
]

function initials(name) {
  const words = name.split(/\s+/).filter(Boolean)
  if (words.length <= 1) return (words[0] ?? '?').slice(0, 2).toUpperCase()
  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
}

function Logo({ branding }) {
  if (branding.logo_url) {
    return (
      <img
        src={branding.logo_url}
        alt=""
        className="h-10 w-10 rounded bg-white/10 object-contain"
      />
    )
  }
  return (
    <div className="flex h-10 w-10 items-center justify-center rounded bg-brand-600 text-sm font-bold text-on-brand">
      {initials(branding.short_name)}
    </div>
  )
}

export default function AppShell({ children }) {
  const branding = useBranding()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Dark backdrop behind the sidebar on small screens */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar text-on-sidebar transition-transform lg:translate-x-0 ${
          menuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 px-5 py-5">
          <Logo branding={branding} />
          <div className="min-w-0 flex-1">
            <div className="truncate font-semibold leading-tight">{branding.short_name}</div>
            <div className="text-xs opacity-70">University ERP</div>
          </div>
          <button
            type="button"
            className="rounded p-1 hover:bg-on-sidebar/10 lg:hidden"
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav aria-label="Main" className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
          {NAV_ITEMS.map(({ label, icon: Icon, active }) => (
            <button
              key={label}
              type="button"
              aria-current={active ? 'page' : undefined}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-on-sidebar/10 ${
                active ? 'bg-on-sidebar/15 font-medium' : 'opacity-90'
              }`}
            >
              <Icon size={18} aria-hidden="true" />
              {label}
            </button>
          ))}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-col lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            className="rounded p-2 hover:bg-slate-100 lg:hidden"
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>

          <div className="relative max-w-xl flex-1">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              type="search"
              placeholder="Search for students, staff, programmes..."
              aria-label="Search"
              className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <button type="button" className="rounded p-2 hover:bg-slate-100" aria-label="Notifications">
              <Bell size={20} />
            </button>
            <div className="flex items-center gap-2 rounded-full bg-slate-100 py-1 pl-1 pr-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-on-brand">
                <User size={16} aria-hidden="true" />
              </div>
              <span className="hidden text-sm text-slate-600 sm:inline">Not signed in</span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6">{children}</main>

        <footer className="border-t border-slate-200 bg-white px-6 py-3 text-xs text-slate-500">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>{branding.university_name}</span>
            {branding.show_powered_by && <span>Powered by Varcity</span>}
          </div>
        </footer>
      </div>
    </div>
  )
}