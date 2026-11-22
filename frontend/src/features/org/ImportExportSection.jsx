import { useRef, useState } from 'react'
import { Download, FileSpreadsheet, Upload } from 'lucide-react'

import SectionCard from '../../components/ui/SectionCard'
import { buttonPrimary, buttonSecondary } from '../../components/ui/styles'
import { importFile, previewImport } from './org-api'

const STATUS_STYLE = {
  create: 'bg-green-100 text-green-800',
  skip: 'bg-slate-200 text-slate-700',
  error: 'bg-red-100 text-red-800',
}
const STATUS_LABEL = { create: 'Create', skip: 'Exists', error: 'Error' }
const MAX_SHOWN = 200

export default function ImportExportSection({ node, ctx }) {
  const { types, index, canEdit, reload } = ctx
  const fileInput = useRef(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [onlyProblems, setOnlyProblems] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const hasChildTypes = types.some((type) => type.allowed_parent_type_ids.includes(node.type_id))
  const hasChildren = (index.childrenOf.get(node.id) ?? []).length > 0
  if (!hasChildTypes && !hasChildren) return null

  const exportUrl = (format) => `/api/v1/org/nodes/${node.id}/export?format=${format}`
  const templateUrl = (format) => `/api/v1/org/import-template?format=${format}`

  function clear() {
    setFile(null)
    setPreview(null)
    setError(null)
  }

  async function handlePick(event) {
    const picked = event.target.files[0]
    event.target.value = ''
    if (!picked) return
    clear()
    setResult(null)
    setBusy(true)
    try {
      const data = await previewImport(node.id, picked)
      setFile(picked)
      setPreview(data)
      setOnlyProblems(data.summary.error > 0)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirm() {
    setBusy(true)
    setError(null)
    try {
      const summary = await importFile(node.id, file)
      setResult(summary)
      clear()
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const rows = preview
    ? preview.rows.filter((row) => !onlyProblems || row.status === 'error')
    : []
  const canConfirm = preview && preview.summary.error === 0 && preview.summary.create > 0

  return (
    <SectionCard
      icon={FileSpreadsheet}
      title="Import and export"
      subtitle={`Work with the entries inside ${node.name} in bulk`}
    >
      <div className="space-y-6">
        <div>
          <p className="text-sm font-medium text-slate-800">Export</p>
          <p className="text-xs text-slate-500">Everything inside {node.name}.</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {[
              ['csv', 'CSV'],
              ['xlsx', 'Excel'],
              ['pdf', 'PDF'],
            ].map(([format, label]) => (
              <a key={format} href={exportUrl(format)} download className={buttonSecondary}>
                <Download size={16} aria-hidden="true" />
                {label}
              </a>
            ))}
          </div>
        </div>

        {canEdit && (
          <div className="border-t border-slate-100 pt-6">
            <p className="text-sm font-medium text-slate-800">Import</p>
            <p className="mt-1 text-xs text-slate-500">
              Columns: <strong>Level</strong>, <strong>Name</strong>, Code (optional) and Parent
              (optional). Leave Parent blank for entries directly inside {node.name}; otherwise
              write the path, for example <em>College of Engineering &gt; School of Computing</em>.
              List parents before the entries inside them. Import only adds entries; ones that
              already exist are skipped.
            </p>

            <div className="mt-3 flex flex-wrap gap-2">
              <a href={templateUrl('xlsx')} download className={buttonSecondary}>
                <Download size={16} aria-hidden="true" />
                Excel template
              </a>
              <a href={templateUrl('csv')} download className={buttonSecondary}>
                <Download size={16} aria-hidden="true" />
                CSV template
              </a>
              <input
                ref={fileInput}
                type="file"
                accept=".csv,.xlsx"
                onChange={handlePick}
                className="hidden"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => fileInput.current.click()}
                className={buttonPrimary}
              >
                <Upload size={16} aria-hidden="true" />
                {busy && !preview ? 'Checking file...' : 'Choose file to import'}
              </button>
            </div>

            {error && (
              <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}
            {result && (
              <p role="status" className="mt-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
                Imported {result.create} {result.create === 1 ? 'entry' : 'entries'}
                {result.skip > 0 ? ` (${result.skip} already existed)` : ''}.
              </p>
            )}

            {preview && (
              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <span className="font-medium text-slate-800">{file.name}</span>
                  <span className="text-green-700">{preview.summary.create} to create</span>
                  <span className="text-slate-500">{preview.summary.skip} already exist</span>
                  <span className={preview.summary.error ? 'text-red-700' : 'text-slate-500'}>
                    {preview.summary.error} with errors
                  </span>
                  <label className="ml-auto flex items-center gap-2 text-xs text-slate-600">
                    <input
                      type="checkbox"
                      checked={onlyProblems}
                      onChange={(event) => setOnlyProblems(event.target.checked)}
                    />
                    Show only problems
                  </label>
                </div>

                {rows.length > 0 && (
                  <div className="max-h-96 overflow-auto rounded-lg border border-slate-200">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-slate-50 text-left text-xs text-slate-500">
                        <tr>
                          <th className="px-3 py-2 font-medium">Row</th>
                          <th className="px-3 py-2 font-medium">Result</th>
                          <th className="px-3 py-2 font-medium">Level</th>
                          <th className="px-3 py-2 font-medium">Name</th>
                          <th className="px-3 py-2 font-medium">Code</th>
                          <th className="px-3 py-2 font-medium">Parent</th>
                          <th className="px-3 py-2 font-medium">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.slice(0, MAX_SHOWN).map((row) => (
                          <tr key={row.row} className="border-t border-slate-100 align-top">
                            <td className="px-3 py-2 text-slate-500">{row.row}</td>
                            <td className="px-3 py-2">
                              <span
                                className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[row.status]}`}
                              >
                                {STATUS_LABEL[row.status]}
                              </span>
                            </td>
                            <td className="px-3 py-2">{row.level}</td>
                            <td className="px-3 py-2">{row.name}</td>
                            <td className="px-3 py-2 font-mono text-xs">{row.code}</td>
                            <td className="px-3 py-2 text-slate-600">{row.parent}</td>
                            <td className="px-3 py-2 text-xs text-slate-600">
                              {row.messages.join(' ')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                {rows.length > MAX_SHOWN && (
                  <p className="text-xs text-slate-500">
                    Showing the first {MAX_SHOWN} of {rows.length} rows.
                  </p>
                )}

                {preview.summary.error > 0 && (
                  <p className="text-xs text-red-700">
                    Fix the errors in your file and choose it again. Nothing is imported until the
                    file is free of errors.
                  </p>
                )}

                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={!canConfirm || busy}
                    onClick={handleConfirm}
                    className={buttonPrimary}
                  >
                    {busy ? 'Importing...' : `Confirm import (${preview.summary.create})`}
                  </button>
                  <button type="button" onClick={clear} className={buttonSecondary}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </SectionCard>
  )
}