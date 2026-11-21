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
  LogOut,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
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

import { useAuth } from '../../auth/auth-context'
import { useBranding } from '../../theme/branding-context'
import BrandLogo from '../BrandLogo'
import { NavLink } from 'react-router-dom'

// Placeholder menu copied from the design mockup. It will later be built
// from the enabled modules and the signed-in user's permissions.
const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
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
  { label: 'Settings', icon: Settings, to: '/settings/organization' },
  { label: 'System Administration', icon: ShieldCheck },
]

// A per-device display preference. Per-user preferences will live on the server later.
const COLLAPSED_KEY = 'varcity.sidebarCollapsed'

function readCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

export default function AppShell({ children }) {
  const branding = useBranding()
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false) // mobile slide-in menu
  const [collapsed, setCollapsed] = useState(readCollapsed) // desktop icon rail

  function toggleCollapsed() {
    const next = !collapsed
    setCollapsed(next)
    try {
      localStorage.setItem(COLLAPSED_KEY, next ? '1' : '0')
    } catch {
      // storage unavailable: the choice just won't be remembered
    }
  }

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
        id="sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar text-on-sidebar transition-[width,transform] duration-200 lg:translate-x-0 ${
          collapsed ? 'lg:w-16' : 'lg:w-64'
        } ${menuOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div
          className={`flex items-center gap-3 px-5 py-5 ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}
        >
          <BrandLogo branding={branding} size="h-10 w-10 shrink-0" />
          <div className={`min-w-0 flex-1 ${collapsed ? 'lg:hidden' : ''}`}>
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
          {NAV_ITEMS.map(({ label, icon: Icon, to }) => {
            const itemClass = `flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-on-sidebar/10 ${
              collapsed ? 'lg:justify-center lg:px-0' : ''
            }`
            const content = (
              <>
                <Icon size={18} aria-hidden="true" className="shrink-0" />
                <span className={collapsed ? 'lg:hidden' : ''}>{label}</span>
              </>
            )

            if (!to) {
              return (
                <button
                  key={label}
                  type="button"
                  title={collapsed ? label : undefined}
                  aria-label={label}
                  className={`${itemClass} opacity-90`}
                >
                  {content}
                </button>
              )
            }

            return (
              <NavLink
                key={label}
                to={to}
                end
                title={collapsed ? label : undefined}
                aria-label={label}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  `${itemClass} ${isActive ? 'bg-on-sidebar/15 font-medium' : 'opacity-90'}`
                }
              >
                {content}
              </NavLink>
            )
          })}
        </nav>
      </aside>

      <div
        className={`flex min-h-screen flex-col transition-[padding] duration-200 ${
          collapsed ? 'lg:pl-16' : 'lg:pl-64'
        }`}
      >
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
          <button
            type="button"
            className="rounded p-2 hover:bg-slate-100 lg:hidden"
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <button
            type="button"
            className="hidden rounded p-2 hover:bg-slate-100 lg:block"
            onClick={toggleCollapsed}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
            aria-controls="sidebar"
          >
            {collapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
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
              <span className="hidden max-w-48 truncate text-sm text-slate-600 sm:inline">
                {user.full_name || user.email}
              </span>
            </div>
            <button
              type="button"
              onClick={logout}
              className="flex items-center gap-1 rounded p-2 text-sm text-slate-600 hover:bg-slate-100"
              aria-label="Sign out"
            >
              <LogOut size={18} aria-hidden="true" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
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