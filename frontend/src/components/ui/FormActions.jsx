import { RotateCcw, Save } from 'lucide-react'

import { buttonPrimary, buttonSecondary } from './styles'

export default function FormActions({ canEdit, dirty, saving, message, onSave, onReset }) {
  return (
    <div className="space-y-3">
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

      {canEdit ? (
        <div className="flex items-center justify-end gap-2">
          {dirty && <span className="mr-auto text-xs text-amber-700">You have unsaved changes.</span>}
          <button
            type="button"
            onClick={onReset}
            disabled={!dirty || saving}
            className={buttonSecondary}
          >
            <RotateCcw size={16} aria-hidden="true" />
            Reset
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={!dirty || saving}
            className={buttonPrimary}
          >
            <Save size={16} aria-hidden="true" />
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      ) : (
        <p className="text-xs text-slate-500">You can view these settings but not change them.</p>
      )}
    </div>
  )
}