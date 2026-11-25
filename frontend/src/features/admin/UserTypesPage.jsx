import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, ChevronRight, Plus, Search, ShieldCheck } from 'lucide-react'

import { usePermissions } from '../../auth/usePermissions'
import PageHeader from '../../components/ui/PageHeader'
import { buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import { listRoles } from './admin-api'
import { ADMIN } from './admin-permissions'

const CUSTOM = 'Custom'
const ORDER = [
  'System administration',
  'General',
  'Executive and institutional leadership',
  'Academic leadership',
  'Academic staff',
  'Academic administration',
  'Examinations',
  'Finance',
  'Procurement and stores',
  'Human resources and administration',
  'Student services',
  'Library, ICT and institutional support',
  'Audit and compliance',
]

function rank(category) {
  if (category === CUSTOM) return 1000
  return ORDER.includes(category) ? ORDER.indexOf(category) : 500
}

export default function UserTypesPage() {
  const { can } = usePermissions()
  const [roles, setRoles] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(() => new Set())

  useEffect(() => {
    listRoles()
      .then(setRoles)
      .catch((err) => setError(err.message))
  }, [])

  const term = query.trim().toLowerCase()

  const groups = useMemo(() => {
    const byCategory = new Map()
    for (const role of roles ?? []) {
      const text = `${role.name} ${role.description ?? ''} ${role.category ?? ''}`.toLowerCase()
      if (term && !text.includes(term)) continue
      const category = role.category ?? CUSTOM
      if (!byCategory.has(category)) byCategory.set(category, [])
      byCategory.get(category).push(role)
    }
    return [...byCategory.entries()].sort(
      (a, b) => rank(a[0]) - rank(b[0]) || a[0].localeCompare(b[0]),
    )
  }, [roles, term])

  function toggle(category) {
    setOpen((previous) => {
      const next = new Set(previous)
      if (next.has(category)) next.delete(category)
      else next.add(category)
      return next
    })
  }

  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {error}
      </p>
    )
  }
  if (!roles) return <div aria-busy="true" />

  const shown = groups.reduce((sum, [, items]) => sum + items.length, 0)

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        icon={ShieldCheck}
        title="User types"
        subtitle="Job functions and the permissions each one starts with"
        actions={
          can(ADMIN.roleManage) && (
            <Link to="/settings/user-types/new" className={buttonPrimary}>
              <Plus size={16} aria-hidden="true" />
              New user type
            </Link>
          )
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-56 flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search user types..."
            aria-label="Search user types"
            className={`${inputClass} mt-0 pl-9`}
          />
        </div>
        <button
          type="button"
          onClick={() => setOpen(new Set(groups.map(([category]) => category)))}
          className={buttonSecondary}
        >
          Expand all
        </button>
        <button type="button" onClick={() => setOpen(new Set())} className={buttonSecondary}>
          Collapse all
        </button>
        <span className="text-xs text-slate-500">
          {shown} {shown === 1 ? 'type' : 'types'} in {groups.length}{' '}
          {groups.length === 1 ? 'category' : 'categories'}
        </span>
      </div>

      {groups.length === 0 && <p className="text-sm text-slate-500">No user types match.</p>}

      <div className="space-y-3">
        {groups.map(([category, items]) => {
          const expanded = term !== '' || open.has(category)
          return (
            <section key={category} className="rounded-xl border border-slate-200 bg-white">
              <button
                type="button"
                onClick={() => toggle(category)}
                aria-expanded={expanded}
                className="flex w-full items-center gap-2 px-5 py-3 text-left"
              >
                {expanded ? (
                  <ChevronDown size={16} aria-hidden="true" />
                ) : (
                  <ChevronRight size={16} aria-hidden="true" />
                )}
                <span className="flex-1 text-sm font-semibold text-slate-900">{category}</span>
                <span className="text-xs text-slate-500">{items.length}</span>
              </button>

              {expanded && (
                <ul className="border-t border-slate-100 px-5">
                  {items.map((role) => (
                    <li
                      key={role.id}
                      className="flex flex-wrap items-center gap-3 border-t border-slate-100 py-2.5 first:border-t-0"
                    >
                      <div className="min-w-0 flex-1">
                        <Link
                          to={`/settings/user-types/${role.id}`}
                          className="font-medium text-brand-700 hover:underline"
                        >
                          {role.name}
                        </Link>
                        {role.description && (
                          <p className="truncate text-xs text-slate-500">{role.description}</p>
                        )}
                      </div>
                      {role.is_system && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          Starter
                        </span>
                      )}
                      {!role.is_active && (
                        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                          Inactive
                        </span>
                      )}
                      <span className="w-36 text-right text-xs text-slate-500">
                        {role.grants_all
                          ? 'All permissions'
                          : role.permissions.length === 0
                            ? 'No permissions yet'
                            : `${role.permissions.length} permissions`}
                      </span>
                      <span className="w-16 text-right text-xs text-slate-500">
                        {role.assignment_count} {role.assignment_count === 1 ? 'user' : 'users'}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )
        })}
      </div>
    </div>
  )
}