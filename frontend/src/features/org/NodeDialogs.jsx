import { useState } from 'react'

import Modal from '../../components/Modal'

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200 disabled:bg-slate-100'

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

function DialogForm({ title, submitLabel, onClose, onSubmit, children }) {
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onSubmit()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {children}
        {error && (
          <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-on-brand hover:bg-brand-700 disabled:opacity-60"
          >
            {submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function AddDialog({ parent, childTypes, onClose, onSave }) {
  const [typeId, setTypeId] = useState(childTypes[0].id)
  const [code, setCode] = useState('')
  const [name, setName] = useState('')

  return (
    <DialogForm
      title={`Add under ${parent.name}`}
      submitLabel="Add"
      onClose={onClose}
      onSubmit={() =>
        onSave({ type_id: typeId, parent_id: parent.id, code: code.trim(), name: name.trim() })
      }
    >
      <Field label="Level">
        <select value={typeId} onChange={(event) => setTypeId(event.target.value)} className={inputClass}>
          {childTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Code" hint="Letters and digits only. Used in registration numbers.">
        <input
          required
          autoFocus
          pattern="[A-Za-z0-9]{1,20}"
          maxLength={20}
          value={code}
          onChange={(event) => setCode(event.target.value)}
          className={`${inputClass} uppercase`}
        />
      </Field>
      <Field label="Name">
        <input
          required
          maxLength={200}
          value={name}
          onChange={(event) => setName(event.target.value)}
          className={inputClass}
        />
      </Field>
    </DialogForm>
  )
}

export function EditDialog({ node, onClose, onSave }) {
  const [code, setCode] = useState(node.code)
  const [name, setName] = useState(node.name)

  return (
    <DialogForm
      title={`Edit ${node.name}`}
      submitLabel="Save"
      onClose={onClose}
      onSubmit={() => onSave({ code: code.trim(), name: name.trim() })}
    >
      <Field label="Name">
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
        hint={node.code_locked ? 'This code has been used and can no longer be changed.' : undefined}
      >
        <input
          required
          disabled={node.code_locked}
          pattern="[A-Za-z0-9]{1,20}"
          maxLength={20}
          value={code}
          onChange={(event) => setCode(event.target.value)}
          className={`${inputClass} uppercase`}
        />
      </Field>
    </DialogForm>
  )
}

export function MoveDialog({ node, candidates, onClose, onSave }) {
  const [parentId, setParentId] = useState(candidates[0].id)

  return (
    <DialogForm
      title={`Move ${node.name}`}
      submitLabel="Move"
      onClose={onClose}
      onSubmit={() => onSave(parentId)}
    >
      <p className="text-sm text-slate-600">Everything inside it moves along with it.</p>
      <Field label="New parent">
        <select
          autoFocus
          value={parentId}
          onChange={(event) => setParentId(event.target.value)}
          className={inputClass}
        >
          {candidates.map((candidate) => (
            <option key={candidate.id} value={candidate.id}>
              {candidate.label}
            </option>
          ))}
        </select>
      </Field>
    </DialogForm>
  )
}