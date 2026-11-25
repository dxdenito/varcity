import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ChevronRight, Copy, Save, Settings2, ShieldCheck, Trash2 } from 'lucide-react'

import { useReauth } from '../../auth/reauth-context'
import { usePermissions } from '../../auth/usePermissions'
import Field from '../../components/ui/Field'
import PageHeader from '../../components/ui/PageHeader'
import SectionCard from '../../components/ui/SectionCard'
import Toggle from '../../components/ui/Toggle'
import {
  buttonDanger,
  buttonPrimary,
  buttonSecondary,
  inputClass,
} from '../../components/ui/styles'
import {
  createRole,
  deleteRole,
  duplicateRole,
  getPermissionTree,
  getRole,
  listRoles,
  updateRole,
} from './admin-api'
import { ADMIN } from './admin-permissions'
import PermissionSummary from './PermissionSummary'
import PermissionTree from './PermissionTree'
import { allCodes, riskByCode } from './permission-tree-utils'

const EMPTY_FORM = { name: '', description: '', category: '', is_active: true }

const toForm = (role) => ({
  name: role.name,
  description: role.description ?? '',
  category: role.category ?? '',
  is_active: role.is_active,
})

const snapshot = (form, codes) =>
  JSON.stringify([form.name, form.description, form.category, form.is_active, [...codes].sort()])

export default function UserTypePage() {
  const { roleId } = useParams()
  const isNew = roleId === 'new'
  const navigate = useNavigate()
  const { can } = usePermissions()
  const { confirmed } = useReauth()

  const [tree, setTree] = useState(null)
  const [categories, setCategories] = useState([])
  const [role, setRole] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [selected, setSelected] = useState(() => new Set())
  const [loadError, setLoadError] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [copyName, setCopyName] = useState('')

  const load = useCallback((data) => {
    setRole(data)
    setForm(toForm(data))
    setSelected(new Set(data.permissions))
  }, [])

  useEffect(() => {
    Promise.all([getPermissionTree(), listRoles()])
      .then(([treeData, roles]) => {
        setTree(treeData)
        setCategories([...new Set(roles.map((item) => item.category).filter(Boolean))].sort())
      })
      .catch((err) => setLoadError(err.message))
  }, [])

  useEffect(() => {
    setMessage(null)
    setRole(null)
    if (isNew) {
      setForm(EMPTY_FORM)
      setSelected(new Set())
      return
    }
    getRole(roleId)
      .then(load)
      .catch((err) => setLoadError(err.message))
  }, [roleId, isNew, load])

  const groups = useMemo(() => tree ?? [], [tree])
  const risks = useMemo(() => riskByCode(groups), [groups])
  const blockAdd = useMemo(
    () => new Set(allCodes(groups).filter((code) => !can(code))),
    [groups, can],
  )
  const baseline = useMemo(
    () => (role ? snapshot(toForm(role), role.permissions) : snapshot(EMPTY_FORM, [])),
    [role],
  )

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!tree || (!isNew && !role)) return <div aria-busy="true" />

  const canManage = can(ADMIN.roleManage)
  const superAdmin = Boolean(role?.grants_all)
  const readOnly = !canManage || superAdmin
  const dirty = snapshot(form, selected) !== baseline

  const chosen = [...selected].filter((code) => risks.has(code))
  const countRisk = (level) => chosen.filter((code) => risks.get(code) === level).length
  const total = risks.size
  const percent = total ? Math.round((chosen.length / total) * 100) : 0

  const setField = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  async function handleSave() {
    setMessage(null)
    setBusy(true)
    const body = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      category: form.category.trim() || null,
      is_active: form.is_active,
      permissions: [...selected],
    }
    try {
      const result = await confirmed(() =>
        isNew ? createRole(body) : updateRole(roleId, body),
      )
      if (isNew) {
        navigate(`/settings/user-types/${result.id}`, { replace: true })
      } else {
        load(result)
        setMessage({ type: 'success', text: 'Changes saved.' })
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleDuplicate(event) {
    event.preventDefault()
    setMessage(null)
    setBusy(true)
    try {
      const copy = await confirmed(() => duplicateRole(role.id, copyName.trim()))
      setCopyName('')
      navigate(`/settings/user-types/${copy.id}`)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${role.name}"? This cannot be undone.`)) return
    setMessage(null)
    setBusy(true)
    try {
      await confirmed(() => deleteRole(role.id))
      navigate('/settings/user-types')
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
      setBusy(false)
    }
  }

  const title = isNew ? 'New user type' : role.name

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-1 text-sm text-slate-500">
          <li>
            <Link to="/settings/user-types" className="hover:text-brand-700 hover:underline">
              User types
            </Link>
          </li>
          <ChevronRight size={14} aria-hidden="true" />
          <li className="font-medium text-slate-900" aria-current="page">
            {title}
          </li>
        </ol>
      </nav>

      <PageHeader
        icon={ShieldCheck}
        title={title}
        subtitle={
          isNew
            ? 'Define a custom job function and what it may do'
            : `${role.category ?? 'Custom'}${role.is_system ? ' - starter user type' : ''}`
        }
        actions={
          <>
            <Link to="/settings/user-types" className={buttonSecondary}>
              <ArrowLeft size={16} aria-hidden="true" />
              Back
            </Link>
            {!readOnly && (
              <button
                type="button"
                onClick={handleSave}
                disabled={!dirty || busy || !form.name.trim()}
                className={buttonPrimary}
              >
                <Save size={16} aria-hidden="true" />
                {busy ? 'Saving...' : 'Save changes'}
              </button>
            )}
          </>
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

      {!canManage && (
        <p className="text-xs text-slate-500">You can view this user type but not change it.</p>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-5">
          <SectionCard title="Details">
            <fieldset disabled={readOnly} className="min-w-0">
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Name" required>
                  <input
                    required
                    maxLength={80}
                    value={form.name}
                    onChange={setField('name')}
                    className={inputClass}
                  />
                </Field>
                <Field label="Category" hint="Pick one or type a new one.">
                  <input
                    list="user-type-categories"
                    maxLength={80}
                    value={form.category}
                    onChange={setField('category')}
                    className={inputClass}
                  />
                  <datalist id="user-type-categories">
                    {categories.map((category) => (
                      <option key={category} value={category} />
                    ))}
                  </datalist>
                </Field>
                <Field label="Description" className="sm:col-span-2">
                  <textarea
                    rows={2}
                    maxLength={300}
                    value={form.description}
                    onChange={setField('description')}
                    className={inputClass}
                  />
                </Field>
                <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 p-3 sm:col-span-2">
                  <div>
                    <p className="text-sm font-medium text-slate-800">Active</p>
                    <p className="text-xs text-slate-500">
                      Inactive types cannot be assigned to anyone new. Existing assignments keep
                      working.
                    </p>
                  </div>
                  <Toggle
                    checked={form.is_active}
                    onChange={(value) => setForm({ ...form, is_active: value })}
                    label="Active"
                  />
                </div>
              </div>
            </fieldset>
          </SectionCard>

          <SectionCard
            icon={ShieldCheck}
            title="Permissions"
            subtitle="Choosing an action also chooses viewing for the same area"
          >
            {superAdmin ? (
              <p className="text-sm text-slate-600">
                Super Admin holds every permission, including ones added by future modules, and
                cannot be changed.
              </p>
            ) : (
              <PermissionTree
                tree={groups}
                selected={selected}
                onChange={setSelected}
                blockAdd={blockAdd}
                readOnly={readOnly}
              />
            )}
          </SectionCard>

          {!isNew && canManage && !superAdmin && (
            <>
              <SectionCard icon={Copy} title="Duplicate" subtitle="Start a new user type from this one">
                <form onSubmit={handleDuplicate} className="flex flex-wrap items-end gap-3">
                  <Field label="Name of the copy" className="min-w-56 flex-1">
                    <input
                      required
                      maxLength={80}
                      value={copyName}
                      onChange={(event) => setCopyName(event.target.value)}
                      className={inputClass}
                    />
                  </Field>
                  <button
                    type="submit"
                    disabled={busy || !copyName.trim()}
                    className={buttonSecondary}
                  >
                    Duplicate
                  </button>
                </form>
              </SectionCard>

              <SectionCard icon={Settings2} title="Manage" subtitle="Remove this user type">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="min-w-0 flex-1 text-xs text-slate-500">
                    {role.is_system
                      ? 'Starter user types cannot be deleted. Mark it inactive instead.'
                      : role.assignment_count > 0
                        ? `This user type is assigned to ${role.assignment_count} ${
                            role.assignment_count === 1 ? 'user' : 'users'
                          }. Remove those assignments first.`
                        : 'Only possible while nobody holds it.'}
                  </p>
                  <button
                    type="button"
                    disabled={busy || role.is_system || role.assignment_count > 0}
                    onClick={handleDelete}
                    className={buttonDanger}
                  >
                    <Trash2 size={14} aria-hidden="true" />
                    Delete
                  </button>
                </div>
              </SectionCard>
            </>
          )}
        </div>

        <div className="space-y-3 lg:sticky lg:top-20 lg:self-start">
          <PermissionSummary
            total={total}
            percent={superAdmin ? 100 : percent}
            segments={[
              {
                label: 'Selected',
                value: superAdmin ? total : chosen.length,
                color: 'brand',
              },
              {
                label: 'Not selected',
                value: superAdmin ? 0 : total - chosen.length,
                color: 'slate',
              },
            ]}
            details={[
              { label: 'Sensitive permissions', value: countRisk('sensitive') },
              { label: 'Critical permissions', value: countRisk('critical') },
              { label: 'Users with this type', value: role?.assignment_count ?? 0 },
            ]}
          />
          {countRisk('critical') > 0 && (
            <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
              This type includes critical permissions. Assigning it to someone will ask for a
              password confirmation.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}