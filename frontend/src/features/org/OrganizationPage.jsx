import { useCallback, useEffect, useMemo, useState } from 'react'

import { useAuth } from '../../auth/auth-context'
import InitializePanel from './InitializePanel'
import { AddDialog, EditDialog, MoveDialog } from './NodeDialogs'
import NodeTree from './NodeTree'
import {
  archiveNode,
  createNode,
  deleteNode,
  loadStructure,
  moveNode,
  unarchiveNode,
  updateNode,
} from './org-api'
import { buildIndex, descendantIds, pathLabel } from './tree'

export default function OrganizationPage() {
  const { user } = useAuth()
  const canEdit = user.is_superuser

  const [data, setData] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [message, setMessage] = useState(null)
  const [dialog, setDialog] = useState(null)

  const reload = useCallback(async () => {
    try {
      setData(await loadStructure())
      setLoadError(null)
    } catch (err) {
      setLoadError(err.message)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const index = useMemo(() => buildIndex(data?.nodes ?? []), [data])

  async function run(action) {
    setMessage(null)
    try {
      await action()
      await reload()
    } catch (err) {
      setMessage(err.message)
    }
  }

  async function save(action) {
    await action()
    setDialog(null)
    await reload()
  }

  function childTypesOf(node) {
    return data.types.filter((type) => type.allowed_parent_type_ids.includes(node.type_id))
  }

  function moveCandidates(node) {
    const nodeType = data.types.find((type) => type.id === node.type_id)
    const excluded = descendantIds(index, node.id)
    return data.nodes
      .filter(
        (candidate) =>
          candidate.status === 'active' &&
          nodeType.allowed_parent_type_ids.includes(candidate.type_id) &&
          !excluded.has(candidate.id) &&
          candidate.id !== node.parent_id,
      )
      .map((candidate) => ({ id: candidate.id, label: pathLabel(index, candidate) }))
  }

  function handleAction(kind, node) {
    setMessage(null)
    if (kind === 'archive') return run(() => archiveNode(node.id))
    if (kind === 'unarchive') return run(() => unarchiveNode(node.id))
    if (kind === 'delete') {
      if (window.confirm(`Delete "${node.name}"? This cannot be undone.`)) {
        return run(() => deleteNode(node.id))
      }
      return undefined
    }
    if (kind === 'move' && moveCandidates(node).length === 0) {
      setMessage('There is nowhere this entry can be moved to.')
      return undefined
    }
    setDialog({ kind, node })
    return undefined
  }

  const closeDialog = () => setDialog(null)

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!data) return <div aria-busy="true" />

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Organization</h1>
        <p className="mt-1 text-sm text-slate-600">
          The structure of your university: campuses, colleges or faculties, schools and
          departments.
        </p>
      </header>

      {data.types.length === 0 ? (
        canEdit ? (
          <InitializePanel onDone={reload} />
        ) : (
          <p className="rounded-lg bg-white p-6 text-sm text-slate-600 shadow-sm">
            The organization structure has not been set up yet. Ask a system administrator.
          </p>
        )
      ) : (
        <>
          <p className="text-sm text-slate-600">
            Levels: {data.types.map((type) => type.name).join(' · ')}
          </p>

          {message && (
            <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {message}
            </p>
          )}

          <section className="rounded-xl bg-white p-4 shadow-sm">
            <NodeTree index={index} types={data.types} canEdit={canEdit} onAction={handleAction} />
          </section>

          {!canEdit && (
            <p className="text-xs text-slate-500">You can view the structure but not change it.</p>
          )}
        </>
      )}

      {dialog?.kind === 'add' && (
        <AddDialog
          parent={dialog.node}
          childTypes={childTypesOf(dialog.node)}
          onClose={closeDialog}
          onSave={(body) => save(() => createNode(body))}
        />
      )}
      {dialog?.kind === 'edit' && (
        <EditDialog
          node={dialog.node}
          onClose={closeDialog}
          onSave={(body) => save(() => updateNode(dialog.node.id, body))}
        />
      )}
      {dialog?.kind === 'move' && (
        <MoveDialog
          node={dialog.node}
          candidates={moveCandidates(dialog.node)}
          onClose={closeDialog}
          onSave={(parentId) => save(() => moveNode(dialog.node.id, parentId))}
        />
      )}
    </div>
  )
}