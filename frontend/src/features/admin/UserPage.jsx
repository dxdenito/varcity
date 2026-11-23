import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronRight, Plus, ShieldCheck, Trash2, UserCog } from 'lucide-react'

import { usePermissions } from '../../auth/usePermissions'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import SectionCard from '../../components/ui/SectionCard'
import { buttonDanger, buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import { ancestorsOf, buildIndex, pathLabel } from '../org/tree'
import { ADMIN } from './admin-permissions'
import { assignRole, getUser, listNodes, listRoles, unassignRole, unlockUser } from './admin-api'

export default function UserPage() {
  const { userId } = useParams()
  const { can, canAt, holdsAll } = usePermissions()

  const [user, setUser] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [roles, setRoles] = useState(null)
  const [nodes, setNodes] = useState(null)
  const [chosenRole, setChosenRole] = useState('')
  const [chosenScope, setChosenScope] = useState('')
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setUser(null)
    getUser(userId)
      .then((data) => {
        setUser(data)
        setLoadError(null)
      })
      .catch((err) => setLoadError(err.message))
  }, [userId])

  useEffect(() => {
    listRoles()
      .then(setRoles)
      .catch(() => setRoles([]))
    listNodes()
      .then(setNodes)
      .catch(() => setNodes([]))
  }, [])

  const index = useMemo(() => buildIndex(nodes ?? []), [nodes])
  const chainOf = (node) => ancestorsOf(index, node).map((item) => item.id)

  const scopes = useMemo(() => {
    const options = (nodes ?? [])
      .filter((node) => node.status === 'active' && canAt(ADMIN.assignRole, chainOf(node)))
      .map((node) => ({ id: node.id, label: pathLabel(index, node) }))
      .sort((a, b) => a.label.localeCompare(b.label))
    return can(ADMIN.assignRole) ? [{ id: '', label: 'Whole university' }, ...options] : options
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, index, can, canAt])

  const roleOptions = (roles ?? []).filter((role) => !role.grants_all || holdsAll)
  const roleId = roleOptions.some((role) => role.id === chosenRole)
    ? chosenRole
    : (roleOptions[0]?.id ?? '')
  const scopeId = scopes.some((scope) => scope.id === chosenScope)
    ? chosenScope
    : (scopes[0]?.id ?? '')

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!user || roles === null || nodes === null) return <div aria-busy="true" />

  function canRemove(assignment) {
    if (!assignment.node_id) return can(ADMIN.assignRole)
    const node = index.byId.get(assignment.node_id)
    return Boolean(node) && canAt(ADMIN.assignRole, chainOf(node))
  }

  async function run(action, successText) {
    setMessage(null)
    setBusy(true)
    try {
      setUser(await action())
      if (successText) setMessage({ type: 'success', text: successText })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  const handleAssign = (event) => {
    event.preventDefault()
    run(() => assignRole(user.id, roleId, scopeId || null), 'Role assigned.')
  }

  const handleUnlock = () =>
    run(async () => {
      await unlockUser(user.id)
      return getUser(user.id)
    }, 'Account unlocked.')

  const displayName = user.full_name || user.email

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-1 text-sm text-slate-500">
          <li>
            <Link to="/admin/users" className="hover:text-brand-700 hover:underline">
              Users
            </Link>
          </li>
          <ChevronRight size={14} aria-hidden="true" />
          <li className="font-medium text-slate-900" aria-current="page">
            {displayName}
          </li>
        </ol>
      </nav>

      <PageHeader icon={UserCog} title={displayName} subtitle={user.email} />

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

      <SectionCard
        title="Account"
        actions={
          user.is_locked &&
          can(ADMIN.unlock) && (
            <button type="button" disabled={busy} onClick={handleUnlock} className={buttonSecondary}>
              Unlock account
            </button>
          )
        }
      >
        <dl className="grid gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs text-slate-500">Name</dt>
            <dd className="mt-0.5 text-slate-900">{user.full_name || 'Not set'}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Email</dt>
            <dd className="mt-0.5 break-all text-slate-900">{user.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Status</dt>
            <dd className="mt-0.5 capitalize text-slate-900">
              {user.is_locked ? 'Locked' : user.status}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Last sign-in</dt>
            <dd className="mt-0.5 text-slate-900">
              {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never'}
            </dd>
          </div>
        </dl>
      </SectionCard>

      <SectionCard
        icon={ShieldCheck}
        title="Roles"
        subtitle="What this user may do, and where"
      >
        {user.is_superuser && (
          <p className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            This account is a system administrator and has every permission regardless of roles.
          </p>
        )}

        {user.assignments.length === 0 ? (
          <p className="text-sm text-slate-500">
            No roles yet. Without a role this user cannot open anything beyond the dashboard.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                  <th className="py-2 pr-3 font-medium">Role</th>
                  <th className="px-3 py-2 font-medium">Where</th>
                  <th className="py-2 pl-3" />
                </tr>
              </thead>
              <tbody>
                {user.assignments.map((assignment) => {
                  const node = assignment.node_id ? index.byId.get(assignment.node_id) : null
                  return (
                    <tr key={assignment.id} className="border-b border-slate-100 last:border-0">
                      <td className="py-2.5 pr-3 font-medium text-slate-900">
                        {assignment.role_name}
                      </td>
                      <td className="px-3 py-2.5 text-slate-600">
                        {assignment.node_id
                          ? node
                            ? pathLabel(index, node)
                            : assignment.node_name
                          : 'Whole university'}
                      </td>
                      <td className="py-2.5 pl-3 text-right">
                        {canRemove(assignment) && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() =>
                              run(() => unassignRole(user.id, assignment.id), 'Role removed.')
                            }
                            className={buttonDanger}
                          >
                            <Trash2 size={14} aria-hidden="true" />
                            Remove
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {scopes.length > 0 && (
          <form
            onSubmit={handleAssign}
            className="mt-5 grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-6"
          >
            {roleOptions.length === 0 ? (
              <p className="text-sm text-slate-600 sm:col-span-6">
                No roles are available to assign. You may need permission to view roles.
              </p>
            ) : (
              <>
                <Field label="Role" className="sm:col-span-3">
                  <select
                    value={roleId}
                    onChange={(event) => setChosenRole(event.target.value)}
                    className={inputClass}
                  >
                    {roleOptions.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field
                  label="Where it applies"
                  hint="A role at an entry covers everything inside it."
                  className="sm:col-span-3"
                >
                  <select
                    value={scopeId}
                    onChange={(event) => setChosenScope(event.target.value)}
                    className={inputClass}
                  >
                    {scopes.map((scope) => (
                      <option key={scope.id} value={scope.id}>
                        {scope.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <div className="sm:col-span-6">
                  <button type="submit" disabled={busy} className={buttonPrimary}>
                    <Plus size={16} aria-hidden="true" />
                    {busy ? 'Assigning...' : 'Assign role'}
                  </button>
                </div>
              </>
            )}
          </form>
        )}
      </SectionCard>
    </div>
  )
}