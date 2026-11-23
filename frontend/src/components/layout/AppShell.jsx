import { useEffect, useMemo, useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Bell, ChevronDown, LogOut, Menu, Search, X } from 'lucide-react'

import { useAuth } from '../../auth/auth-context'
import { usePermissions } from '../../auth/usePermissions'
import { NAV_ITEMS, visibleItems } from '../../navigation'
import { useBranding } from '../../theme/branding-context'
import BrandLogo from '../BrandLogo'

const COLLAPSED_KEY = 'varcity.sidebarCollapsed'

const isDesktop = () => window.matchMedia('(min-width: 1024px)').matches

function readCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

function NavEntry({ item, collapsed, openGroups, toggleGroup, closeMenu }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { label, icon: Icon, to, children } = item

  const itemClass = `flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-on-sidebar/10 ${
    collapsed ? 'lg:justify-center lg:px-0' : ''
  }`
  const labelClass = collapsed ? 'lg:hidden' : ''
  const icon = <Icon size={18} aria-hidden="true" className="shrink-0" />

  if (children) {
    const isOpen = openGroups.has(label)
    const isActive = pathname.startsWith(to)
    const handleClick = () => {
      if (collapsed && isDesktop()) navigate(children[0].to)
      else toggleGroup(label)
    }

    return (
      <div>
        <button
          type="button"
          onClick={handleClick}
          aria-expanded={isOpen}
          title={collapsed ? label : undefined}
          className={`${itemClass} ${isActive ? 'bg-on-sidebar/10 font-medium' : 'opacity-90'}`}
        >
          {icon}
          <span className={`flex-1 ${labelClass}`}>{label}</span>
          <ChevronDown
            size={14}
            aria-hidden="true"
            className={`transition-transform ${isOpen ? 'rotate-180' : ''} ${labelClass}`}
          />
        </button>
        {isOpen && (
          <ul className={`mt-0.5 space-y-0.5 pl-9 ${collapsed ? 'lg:hidden' : ''}`}>
            {children.map((child) => (
              <li key={child.to}>
                <NavLink
                  to={child.to}
                  onClick={closeMenu}
                  className={({ isActive: active }) =>
                    `block rounded-lg px-3 py-1.5 text-sm hover:bg-on-sidebar/10 ${
                      active ? 'bg-on-sidebar/15 font-medium' : 'opacity-80'
                    }`
                  }
                >
                  {child.label}
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  if (!to) {
    return (
      <button
        type="button"
        title={collapsed ? label : undefined}
        aria-label={label}
        className={`${itemClass} opacity-90`}
      >
        {icon}
        <span className={labelClass}>{label}</span>
      </button>
    )
  }

  return (
    <NavLink
      to={to}
      end
      title={collapsed ? label : undefined}
      aria-label={label}
      onClick={closeMenu}
      className={({ isActive }) =>
        `${itemClass} ${isActive ? 'bg-on-sidebar/15 font-medium' : 'opacity-90'}`
      }
    >
      {icon}
      <span className={labelClass}>{label}</span>
    </NavLink>
  )
}

export default function AppShell({ children }) {
  const branding = useBranding()
  const { user, logout } = useAuth()
  const { canAnywhere } = usePermissions()
  const navItems = useMemo(() => visibleItems(NAV_ITEMS, canAnywhere), [canAnywhere])
  const { pathname } = useLocation()

  const [menuOpen, setMenuOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(readCollapsed)
  const [openGroups, setOpenGroups] = useState(
    () =>
      new Set(
        NAV_ITEMS.filter((item) => item.children && pathname.startsWith(item.to)).map(
          (item) => item.label,
        ),
      ),
  )

  useEffect(() => {
    for (const item of NAV_ITEMS) {
      if (item.children && pathname.startsWith(item.to)) {
        setOpenGroups((previous) =>
          previous.has(item.label) ? previous : new Set(previous).add(item.label),
        )
      }
    }
  }, [pathname])

  function toggleGroup(label) {
    setOpenGroups((previous) => {
      const next = new Set(previous)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }

  function handleHamburger() {
    if (!isDesktop()) {
      setMenuOpen((open) => !open)
      return
    }
    const next = !collapsed
    setCollapsed(next)
    try {
      localStorage.setItem(COLLAPSED_KEY, next ? '1' : '0')
    } catch {
      // storage unavailable: the choice just won't be remembered
    }
  }

  const displayName = user.full_name || user.email
  const closeMenu = () => setMenuOpen(false)

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={closeMenu}
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
          className={`flex items-center gap-3 px-4 py-5 ${collapsed ? 'lg:justify-center lg:px-0' : ''}`}
        >
          <BrandLogo branding={branding} size="h-14 w-14 shrink-0" />
          <div className={`min-w-0 flex-1 ${collapsed ? 'lg:hidden' : ''}`}>
            <div className="truncate font-semibold leading-tight">{branding.short_name}</div>
            <div className="text-xs opacity-70">University ERP</div>
          </div>
          <button
            type="button"
            className="rounded p-1 hover:bg-on-sidebar/10 lg:hidden"
            onClick={closeMenu}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav aria-label="Main" className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-4">
          {navItems.map((item) => (
            <NavEntry
              key={item.label}
              item={item}
              collapsed={collapsed}
              openGroups={openGroups}
              toggleGroup={toggleGroup}
              closeMenu={closeMenu}
            />
          ))}
        </nav>
      </aside>

      <div
        className={`flex min-h-screen flex-col transition-[padding] duration-200 ${
          collapsed ? 'lg:pl-16' : 'lg:pl-64'
        }`}
      >
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-2.5 text-slate-700">
          <button
            type="button"
            onClick={handleHamburger}
            aria-label="Toggle menu"
            aria-controls="sidebar"
            className="rounded-lg p-2 hover:bg-slate-100"
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
              placeholder="Search for students, staff, records..."
              aria-label="Search"
              className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
            />
          </div>

          <div className="ml-auto flex items-center gap-1">
            <button type="button" className="rounded-lg p-2 hover:bg-slate-100" aria-label="Notifications">
              <Bell size={20} />
            </button>
            <div className="flex items-center gap-2 pl-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-on-brand">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <div className="hidden leading-tight sm:block">
                <div className="max-w-40 truncate text-sm font-medium text-slate-900">
                  {displayName}
                </div>
                {user.is_superuser && <div className="text-xs text-slate-500">System administrator</div>}
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="flex items-center gap-1 rounded-lg p-2 text-sm hover:bg-slate-100"
              aria-label="Sign out"
            >
              <LogOut size={18} aria-hidden="true" />
              <span className="hidden md:inline">Sign out</span>
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