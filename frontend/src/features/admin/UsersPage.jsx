import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Search, UserCog } from 'lucide-react'

import PageHeader from '../../components/ui/PageHeader'
import SectionCard from '../../components/ui/SectionCard'
import { buttonSecondary, inputClass } from '../../components/ui/styles'
import { listUsers } from './admin-api'

const PAGE_SIZE = 25

function describe(assignment) {
  return assignment.node_name
    ? `${assignment.role_name} at ${assignment.node_name}`
    : assignment.role_name
}

function Roles({ user }) {
  if (user.is_superuser) return <span className="text-xs text-slate-600">All access</span>
  const shown = user.assignments.slice(0, 2)
  if (shown.length === 0) return <span className="text-xs text-slate-400">None</span>
  return (
    <div className="flex flex-wrap gap-1">
      {shown.map((assignment) => (
        <span
          key={assignment.id}
          className="rounded-full bg-brand-50 px-2 py-0.5 text-xs text-brand-800"
        >
          {describe(assignment)}
        </span>
      ))}
      {user.assignments.length > 2 && (
        <span className="text-xs text-slate-500">+{user.assignments.length - 2} more</span>
      )}
    </div>
  )
}

function StatusBadge({ user }) {
  if (user.is_locked) {
    return <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-800">Locked</span>
  }
  if (user.status !== 'active') {
    return (
      <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs capitalize text-slate-700">
        {user.status}
      </span>
    )
  }
  return <span className="text-xs text-slate-500">Active</span>
}

export default function UsersPage() {
  const [input, setInput] = useState('')
  const [term, setTerm] = useState('')
  const [offset, setOffset] = useState(0)
  const [page, setPage] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      setTerm(input.trim())
      setOffset(0)
    }, 300)
    return () => clearTimeout(timer)
  }, [input])

  useEffect(() => {
    let cancelled = false
    listUsers({ q: term, limit: PAGE_SIZE, offset })
      .then((data) => {
        if (cancelled) return
        setPage(data)
        setError(null)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [term, offset])

  const from = page && page.total > 0 ? offset + 1 : 0
  const to = page ? Math.min(offset + PAGE_SIZE, page.total) : 0

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader
        icon={UserCog}
        title="Users"
        subtitle="Sign-in accounts and the roles they hold"
      />

      <SectionCard
        title="All users"
        actions={
          <div className="relative w-64 max-w-full">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />
            <input
              type="search"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Search name or email"
              aria-label="Search users"
              className={`${inputClass} mt-0 pl-9`}
            />
          </div>
        }
      >
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {!error && !page && <div aria-busy="true" />}

        {page && page.items.length === 0 && (
          <p className="text-sm text-slate-500">No users match your search.</p>
        )}

        {page && page.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                  <th className="py-2 pr-3 font-medium">Name</th>
                  <th className="px-3 py-2 font-medium">Email</th>
                  <th className="px-3 py-2 font-medium">Roles</th>
                  <th className="px-3 py-2 font-medium">Last sign-in</th>
                  <th className="py-2 pl-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-slate-100 align-top last:border-0 hover:bg-slate-50"
                  >
                    <td className="py-2.5 pr-3">
                      <Link
                        to={`/settings/users/${user.id}`}
                        className="font-medium text-brand-700 hover:underline"
                      >
                        {user.full_name || user.email}
                      </Link>
                    </td>
                    <td className="px-3 py-2.5 text-slate-600">{user.email}</td>
                    <td className="px-3 py-2.5">
                      <Roles user={user} />
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-600">
                      {user.last_login_at
                        ? new Date(user.last_login_at).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="py-2.5 pl-3">
                      <StatusBadge user={user} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {page && page.total > PAGE_SIZE && (
          <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {from}-{to} of {page.total}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                className={buttonSecondary}
              >
                <ChevronLeft size={16} aria-hidden="true" />
                Previous
              </button>
              <button
                type="button"
                disabled={to >= page.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                className={buttonSecondary}
              >
                Next
                <ChevronRight size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  )
}