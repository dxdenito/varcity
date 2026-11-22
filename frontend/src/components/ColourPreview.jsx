import { readableTextColor } from '../lib/color'

export default function ColourPreview({ primary, sidebar, label }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200" aria-hidden="true">
      <div className="flex h-24">
        <div
          className="flex w-1/3 flex-col gap-2 p-3 text-xs"
          style={{ backgroundColor: sidebar, color: readableTextColor(sidebar) }}
        >
          <span className="truncate font-semibold">{label || 'Short name'}</span>
          <span className="h-2 w-3/4 rounded bg-current opacity-30" />
          <span className="h-2 w-1/2 rounded bg-current opacity-30" />
        </div>
        <div className="flex flex-1 flex-col items-start justify-center gap-2 bg-slate-50 p-4">
          <span className="h-2 w-24 rounded bg-slate-300" />
          <span
            className="rounded-md px-3 py-1.5 text-xs font-medium"
            style={{ backgroundColor: primary, color: readableTextColor(primary) }}
          >
            Primary button
          </span>
        </div>
      </div>
    </div>
  )
}