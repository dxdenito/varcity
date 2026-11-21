import { useMemo, useState } from 'react'
import {
  Archive,
  ArchiveRestore,
  ArrowRightLeft,
  ChevronDown,
  ChevronRight,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'

function IconButton({ label, onClick, children }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      className="rounded p-1.5 text-slate-500 hover:bg-slate-200 hover:text-slate-900"
    >
      {children}
    </button>
  )
}

function Row({ node, depth, ctx }) {
  const { index, typeById, parentTypeIds, canEdit, onAction, collapsed, toggle } = ctx
  const children = index.childrenOf.get(node.id) ?? []
  const isOpen = !collapsed.has(node.id)
  const isTop = node.parent_id === null
  const archived = node.status === 'archived'

  return (
    <li>
      <div
        className={`flex items-center gap-2 rounded-lg py-1.5 pr-2 hover:bg-slate-50 ${
          archived ? 'opacity-60' : ''
        }`}
        style={{ paddingLeft: `${depth * 22 + 8}px` }}
      >
        {children.length > 0 ? (
          <button
            type="button"
            onClick={() => toggle(node.id)}
            aria-label={isOpen ? `Collapse ${node.name}` : `Expand ${node.name}`}
            aria-expanded={isOpen}
            className="rounded p-0.5 text-slate-500 hover:bg-slate-200"
          >
            {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        ) : (
          <span className="w-5" />
        )}

        <span className="rounded bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
          {typeById.get(node.type_id)?.name}
        </span>
        <span className="font-medium text-slate-900">{node.name}</span>
        <span className="font-mono text-xs text-slate-500">{node.code}</span>
        {archived && (
          <span className="rounded bg-slate-200 px-2 py-0.5 text-xs text-slate-600">Archived</span>
        )}

        {canEdit && (
          <div className="ml-auto flex shrink-0 gap-0.5">
            {parentTypeIds.has(node.type_id) && !archived && (
              <IconButton label={`Add under ${node.name}`} onClick={() => onAction('add', node)}>
                <Plus size={16} />
              </IconButton>
            )}
            <IconButton label={`Edit ${node.name}`} onClick={() => onAction('edit', node)}>
              <Pencil size={16} />
            </IconButton>
            {!isTop && !archived && (
              <IconButton label={`Move ${node.name}`} onClick={() => onAction('move', node)}>
                <ArrowRightLeft size={16} />
              </IconButton>
            )}
            {!isTop && (
              <IconButton
                label={archived ? `Restore ${node.name}` : `Archive ${node.name}`}
                onClick={() => onAction(archived ? 'unarchive' : 'archive', node)}
              >
                {archived ? <ArchiveRestore size={16} /> : <Archive size={16} />}
              </IconButton>
            )}
            {!isTop && (
              <IconButton label={`Delete ${node.name}`} onClick={() => onAction('delete', node)}>
                <Trash2 size={16} />
              </IconButton>
            )}
          </div>
        )}
      </div>

      {children.length > 0 && isOpen && (
        <ul>
          {children.map((child) => (
            <Row key={child.id} node={child} depth={depth + 1} ctx={ctx} />
          ))}
        </ul>
      )}
    </li>
  )
}

export default function NodeTree({ index, types, canEdit, onAction }) {
  const [collapsed, setCollapsed] = useState(() => new Set())

  const typeById = useMemo(() => new Map(types.map((type) => [type.id, type])), [types])
  const parentTypeIds = useMemo(
    () => new Set(types.flatMap((type) => type.allowed_parent_type_ids)),
    [types],
  )

  function toggle(id) {
    setCollapsed((previous) => {
      const next = new Set(previous)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const ctx = { index, typeById, parentTypeIds, canEdit, onAction, collapsed, toggle }

  return (
    <ul>
      {index.roots.map((node) => (
        <Row key={node.id} node={node} depth={0} ctx={ctx} />
      ))}
    </ul>
  )
}