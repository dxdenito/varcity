import { useState } from 'react'
import { Info, Pencil } from 'lucide-react'

import Field from '../../components/ui/Field'
import SectionCard from '../../components/ui/SectionCard'
import { buttonPrimary, buttonSecondary, inputClass } from '../../components/ui/styles'
import { updateNode } from './org-api'
import { ORG } from './org-permissions'

export default function DetailsSection({ node, ctx }) {
  const { typeById, canNode, reload } = ctx
  const canEdit = canNode(ORG.update, node)
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(node.name)
  const [code, setCode] = useState(node.code ?? '')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  function startEditing() {
    setName(node.name)
    setCode(node.code ?? '')
    setError(null)
    setEditing(true)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await updateNode(node.id, { name: name.trim(), code: code.trim() || null })
      setEditing(false)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <SectionCard
      icon={Info}
      title="Details"
      actions={
        canEdit &&
        !editing && (
          <button type="button" onClick={startEditing} className={buttonSecondary}>
            <Pencil size={14} aria-hidden="true" />
            Edit
          </button>
        )
      }
    >
      {editing ? (
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" required>
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
            hint={
              node.code_locked
                ? 'This code has been used and can no longer be changed.'
                : 'Optional. Letters and digits only.'
            }
          >
            <input
              disabled={node.code_locked}
              pattern="[A-Za-z0-9]{1,20}"
              maxLength={20}
              value={code}
              onChange={(event) => setCode(event.target.value)}
              className={`${inputClass} uppercase`}
            />
          </Field>

          {error && (
            <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 sm:col-span-2">
              {error}
            </p>
          )}

          <div className="flex gap-2 sm:col-span-2">
            <button type="submit" disabled={busy} className={buttonPrimary}>
              {busy ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={() => setEditing(false)} className={buttonSecondary}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <dl className="grid gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs text-slate-500">Name</dt>
            <dd className="mt-0.5 font-medium text-slate-900">{node.name}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Level</dt>
            <dd className="mt-0.5 text-slate-900">{typeById.get(node.type_id)?.name}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Code</dt>
            <dd className="mt-0.5 font-mono text-slate-900">{node.code ?? 'None'}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Status</dt>
            <dd className="mt-0.5 text-slate-900">
              {node.status === 'archived' ? 'Archived' : 'Active'}
            </dd>
          </div>
        </dl>
      )}
    </SectionCard>
  )
}