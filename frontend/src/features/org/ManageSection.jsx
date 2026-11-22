import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings2 } from 'lucide-react'

import SectionCard from '../../components/ui/SectionCard'
import { buttonDanger, buttonSecondary, inputClass } from '../../components/ui/styles'
import { archiveNode, deleteNode, moveNode, unarchiveNode } from './org-api'
import { descendantIds, pathLabel } from './tree'

export default function ManageSection({ node, ctx }) {
  const { nodes, index, typeById, reload } = ctx
  const navigate = useNavigate()
  const isTop = node.parent_id === null
  const archived = node.status === 'archived'

  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [chosenParent, setChosenParent] = useState('')

  const candidates = useMemo(() => {
    const nodeType = typeById.get(node.type_id)
    const excluded = descendantIds(index, node.id)
    return nodes
      .filter(
        (candidate) =>
          candidate.status === 'active' &&
          nodeType.allowed_parent_type_ids.includes(candidate.type_id) &&
          !excluded.has(candidate.id) &&
          candidate.id !== node.parent_id,
      )
      .map((candidate) => ({ id: candidate.id, label: pathLabel(index, candidate) }))
  }, [nodes, index, typeById, node])

  const parentId = candidates.some((candidate) => candidate.id === chosenParent)
    ? chosenParent
    : (candidates[0]?.id ?? '')

  async function run(action, successText) {
    setMessage(null)
    setBusy(true)
    try {
      await action()
      await reload()
      if (successText) setMessage({ type: 'success', text: successText })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${node.name}"? This cannot be undone.`)) return
    setMessage(null)
    setBusy(true)
    try {
      await deleteNode(node.id)
      navigate(`/settings/organization/${node.parent_id}`)
      await reload()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
      setBusy(false)
    }
  }

  return (
    <SectionCard icon={Settings2} title="Manage" subtitle="Move, archive or delete this entry">
      {message && (
        <p
          role={message.type === 'error' ? 'alert' : 'status'}
          className={`mb-4 rounded-lg p-3 text-sm ${
            message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
          }`}
        >
          {message.text}
        </p>
      )}

      {isTop ? (
        <p className="text-sm text-slate-500">
          The institution&apos;s top-level entry cannot be moved, archived or deleted.
        </p>
      ) : (
        <div className="divide-y divide-slate-100">
          {!archived && (
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-800">Move</p>
                <p className="text-xs text-slate-500">
                  Everything inside it moves along with it.
                </p>
              </div>
              {candidates.length === 0 ? (
                <p className="text-xs text-slate-500">There is nowhere it can be moved to.</p>
              ) : (
                <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                  <select
                    value={parentId}
                    onChange={(event) => setChosenParent(event.target.value)}
                    aria-label="New parent"
                    className={`${inputClass} mt-0 sm:w-72`}
                  >
                    {candidates.map((candidate) => (
                      <option key={candidate.id} value={candidate.id}>
                        {candidate.label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => run(() => moveNode(node.id, parentId), 'Moved.')}
                    className={buttonSecondary}
                  >
                    Move
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 py-4">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-800">
                {archived ? 'Restore' : 'Archive'}
              </p>
              <p className="text-xs text-slate-500">
                {archived
                  ? 'Make it active again. Its parent must be active.'
                  : 'Hide it from new work but keep its history. Everything inside must be archived first.'}
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => run(() => (archived ? unarchiveNode(node.id) : archiveNode(node.id)))}
              className={buttonSecondary}
            >
              {archived ? 'Restore' : 'Archive'}
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-4">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-800">Delete</p>
              <p className="text-xs text-slate-500">
                Only possible when nothing depends on it. Otherwise archive it instead.
              </p>
            </div>
            <button type="button" disabled={busy} onClick={handleDelete} className={buttonDanger}>
              Delete
            </button>
          </div>
        </div>
      )}
    </SectionCard>
  )
}