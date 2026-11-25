import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, ChevronRight, Info, Search } from 'lucide-react'

import { buttonSecondary, inputClass } from '../../components/ui/styles'
import { applyToggle, codesOf } from './permission-tree-utils'

const EMPTY_SET = new Set()
const EMPTY_MAP = new Map()
const RISK_STYLE = {
  sensitive: 'bg-amber-100 text-amber-800',
  critical: 'bg-red-100 text-red-800',
}

function TriCheckbox({ checked, indeterminate = false, disabled, onChange, label }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate
  }, [indeterminate])

  return (
    <input
      ref={ref}
      type="checkbox"
      checked={checked}
      disabled={disabled}
      onChange={(event) => onChange(event.target.checked)}
      aria-label={label}
      className="h-4 w-4 shrink-0 rounded border-slate-300 accent-brand-600 disabled:opacity-60"
    />
  )
}

export default function PermissionTree({
  tree,
  selected,
  onChange,
  blockAdd = EMPTY_SET,
  locked = EMPTY_MAP,
  readOnly = false,
}) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(() => new Set())
  const term = query.trim().toLowerCase()

  const visible = useMemo(() => {
    if (!term) return tree
    return tree
      .map((group) => ({
        ...group,
        resources: group.resources
          .map((resource) => ({
            ...resource,
            permissions: resource.permissions.filter(
              (p) =>
                p.description.toLowerCase().includes(term) ||
                p.code.includes(term) ||
                resource.label.toLowerCase().includes(term) ||
                group.label.toLowerCase().includes(term),
            ),
          }))
          .filter((resource) => resource.permissions.length > 0),
      }))
      .filter((group) => group.resources.length > 0)
  }, [tree, term])

  const isOn = (code) => selected.has(code) || locked.has(code)
  const cannotChange = (code) =>
    readOnly || locked.has(code) || (blockAdd.has(code) && !selected.has(code))

  function toggle(codes, checked) {
    const allowed = codes.filter((code) =>
      checked ? !locked.has(code) && !blockAdd.has(code) : !locked.has(code),
    )
    if (allowed.length) onChange(applyToggle(tree, selected, allowed, checked))
  }

  function toggleOpen(module) {
    setOpen((previous) => {
      const next = new Set(previous)
      if (next.has(module)) next.delete(module)
      else next.add(module)
      return next
    })
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-48 flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search permissions..."
            aria-label="Search permissions"
            className={`${inputClass} mt-0 pl-9`}
          />
        </div>
        <button
          type="button"
          onClick={() => setOpen(new Set(tree.map((group) => group.module)))}
          className={buttonSecondary}
        >
          Expand all
        </button>
        <button type="button" onClick={() => setOpen(new Set())} className={buttonSecondary}>
          Collapse all
        </button>
      </div>

      {visible.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No permissions match your search.</p>
      ) : (
        <ul className="mt-4 divide-y divide-slate-100 rounded-lg border border-slate-200">
          {visible.map((group) => {
            const codes = codesOf(tree.find((item) => item.module === group.module))
            const on = codes.filter(isOn).length
            const expanded = term !== '' || open.has(group.module)

            return (
              <li key={group.module}>
                <div className="flex items-center gap-3 px-3 py-2.5">
                  <TriCheckbox
                    checked={codes.length > 0 && on === codes.length}
                    indeterminate={on > 0 && on < codes.length}
                    disabled={codes.every(cannotChange)}
                    onChange={(checked) => toggle(codes, checked)}
                    label={`Select all in ${group.label}`}
                  />
                  <button
                    type="button"
                    onClick={() => toggleOpen(group.module)}
                    aria-expanded={expanded}
                    className="flex min-w-0 flex-1 items-center gap-2 text-left"
                  >
                    {expanded ? (
                      <ChevronDown size={16} aria-hidden="true" />
                    ) : (
                      <ChevronRight size={16} aria-hidden="true" />
                    )}
                    <span className="text-sm font-medium text-slate-900">{group.label}</span>
                  </button>
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600">
                    {on} of {codes.length}
                  </span>
                </div>

                {expanded && (
                  <div className="border-t border-slate-100 bg-slate-50/60 pb-3 pl-10 pr-3">
                    {group.resources.map((resource) => (
                      <div key={resource.resource} className="pt-3">
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          {resource.label}
                        </p>
                        <ul className="mt-1">
                          {resource.permissions.map((p) => (
                            <li key={p.code} className="flex items-start gap-3 py-1.5">
                              <TriCheckbox
                                checked={isOn(p.code)}
                                disabled={cannotChange(p.code)}
                                onChange={(checked) => toggle([p.code], checked)}
                                label={p.description}
                              />
                              <div className="min-w-0 flex-1">
                                <span className="text-sm text-slate-800">{p.description}</span>
                                {locked.has(p.code) && (
                                  <span className="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700">
                                    {locked.get(p.code)}
                                  </span>
                                )}
                                {RISK_STYLE[p.risk] && (
                                  <span
                                    className={`ml-2 rounded-full px-2 py-0.5 text-xs ${RISK_STYLE[p.risk]}`}
                                  >
                                    {p.risk}
                                  </span>
                                )}
                              </div>
                              <span title={`${p.code}\nRisk: ${p.risk}`}>
                                <Info size={14} className="text-slate-400" aria-label={p.code} />
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}