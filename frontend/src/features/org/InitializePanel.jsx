import { useState } from 'react'

import { initializeStructure } from './org-api'

const TEMPLATES = [
  {
    value: 'college',
    title: 'Colleges',
    chain: 'University → Campus → College → School → Department',
  },
  {
    value: 'faculty',
    title: 'Faculties',
    chain: 'University → Campus → Faculty → School → Department',
  },
]

export default function InitializePanel({ onDone }) {
  const [template, setTemplate] = useState('college')
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await initializeStructure(template, code.trim())
      await onDone()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-6 rounded-xl bg-white p-6 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Set up your organization</h2>
        <p className="mt-1 text-sm text-slate-600">
          Choose how your university names its levels. You can add campuses, colleges or
          faculties, schools and departments afterwards.
        </p>
      </div>

      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-slate-700">Structure</legend>
        {TEMPLATES.map((option) => (
          <label
            key={option.value}
            className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 ${
              template === option.value ? 'border-brand-500 bg-brand-50' : 'border-slate-200'
            }`}
          >
            <input
              type="radio"
              name="template"
              value={option.value}
              checked={template === option.value}
              onChange={() => setTemplate(option.value)}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium text-slate-900">{option.title}</span>
              <span className="block text-xs text-slate-500">{option.chain}</span>
            </span>
          </label>
        ))}
      </fieldset>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">Institution code</span>
        <input
          required
          pattern="[A-Za-z0-9]{1,20}"
          maxLength={20}
          value={code}
          onChange={(event) => setCode(event.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm uppercase outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-200"
        />
        <span className="mt-1 block text-xs text-slate-500">
          Letters and digits only, for example KU. It is used in registration numbers and cannot be
          changed once used.
        </span>
      </label>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-on-brand hover:bg-brand-700 disabled:opacity-60"
      >
        {busy ? 'Creating...' : 'Create structure'}
      </button>
    </form>
  )
}