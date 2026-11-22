import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Building2, Plus } from 'lucide-react'

import Field from '../../components/ui/Field'
import SectionCard from '../../components/ui/SectionCard'
import { buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import { createNode } from './org-api'

export default function ChildrenSection({ node, ctx }) {
  const { types, index, typeById, canEdit, reload } = ctx
  const children = index.childrenOf.get(node.id) ?? []
  const childTypes = types.filter((type) => type.allowed_parent_type_ids.includes(node.type_id))

  const [adding, setAdding] = useState(false)
  const [typeId, setTypeId] = useState(childTypes[0]?.id ?? '')
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (childTypes.length === 0 && children.length === 0) return null

  const archived = node.status === 'archived'
  const canAdd = canEdit && !archived && childTypes.length > 0
  const title = childTypes.map((type) => type.plural_name).join(' and ') || 'Contents'
  const addLabel = childTypes.length === 1 ? `Add ${childTypes[0].name}` : 'Add'

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await createNode({
        type_id: typeId,
        parent_id: node.id,
        code: code.trim() || null,
        name: name.trim(),
      })
      setName('')
      setCode('')
      setAdding(false)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <SectionCard
      icon={Building2}
      title={title}
      subtitle={`Directly inside ${node.name}`}
      actions={
        canAdd &&
        !adding && (
          <button type="button" onClick={() => setAdding(true)} className={buttonPrimary}>
            <Plus size={16} aria-hidden="true" />
            {addLabel}
          </button>
        )
      }
    >
      {adding && (
        <form
          onSubmit={handleSubmit}
          className="mb-5 grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-6"
        >
          {childTypes.length > 1 && (
            <Field label="Level" className="sm:col-span-2">
              <select
                value={typeId}
                onChange={(event) => setTypeId(event.target.value)}
                className={inputClass}
              >
                {childTypes.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </Field>
          )}
          <Field
            label="Name"
            required
            className={childTypes.length > 1 ? 'sm:col-span-4' : 'sm:col-span-4'}
          >
            <input
              required
              autoFocus
              maxLength={200}
              value={name}
              onChange={(event) => setName(event.target.value)}
              className={inputClass}
            />
          </Field>
          <Field
            label="Code"
            hint="Optional. Letters and digits only. Needed where registration numbers use it, such as a satellite campus."
            className="sm:col-span-6"
          >
            <input
              pattern="[A-Za-z0-9]{1,20}"
              maxLength={20}
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className={`${inputClass} uppercase sm:max-w-48`}
            />
          </Field>

          {error && (
            <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 sm:col-span-6">
              {error}
            </p>
          )}

          <div className="flex gap-2 sm:col-span-6">
            <button type="submit" disabled={busy} className={buttonPrimary}>
              {busy ? 'Adding...' : 'Add'}
            </button>
            <button
              type="button"
              onClick={() => {
                setAdding(false)
                setError(null)
              }}
              className={buttonSecondary}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {children.length === 0 ? (
        <p className="text-sm text-slate-500">
          Nothing here yet.{canAdd ? ' Use the button above to add the first one.' : ''}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="py-2 pr-3 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Level</th>
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 text-right font-medium">Inside</th>
                <th className="py-2 pl-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {children.map((child) => (
                <tr key={child.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="py-2.5 pr-3">
                    <Link
                      to={`/settings/organization/${child.id}`}
                      className="font-medium text-brand-700 hover:underline"
                    >
                      {child.name}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 text-slate-600">{typeById.get(child.type_id)?.name}</td>
                  <td className="px-3 py-2.5 font-mono text-xs text-slate-600">{child.code ?? '—'}</td>
                  <td className="px-3 py-2.5 text-right text-slate-600">
                    {index.childrenOf.get(child.id)?.length ?? 0}
                  </td>
                  <td className="py-2.5 pl-3">
                    {child.status === 'archived' ? (
                      <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                        Archived
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500">Active</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {archived && canEdit && (
        <p className="mt-4 text-xs text-slate-500">
          This entry is archived. Restore it before adding anything inside it.
        </p>
      )}
    </SectionCard>
  )
}