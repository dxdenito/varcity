const RADIUS = 40
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const COLORS = {
  brand: { stroke: 'stroke-brand-600', dot: 'bg-brand-600' },
  emerald: { stroke: 'stroke-emerald-500', dot: 'bg-emerald-500' },
  slate: { stroke: 'stroke-slate-300', dot: 'bg-slate-300' },
}

export default function PermissionSummary({ total, percent, segments, details = [] }) {
  let offset = 0

  return (
    <aside className="rounded-xl border border-slate-200 bg-white">
      <h2 className="border-b border-slate-100 px-5 py-3 text-sm font-semibold text-slate-900">
        Permission summary
      </h2>
      <div className="p-5">
        <div className="flex items-center gap-5">
          <svg
            viewBox="0 0 100 100"
            className="h-28 w-28 shrink-0"
            role="img"
            aria-label={`${percent}% of ${total} permissions selected`}
          >
            {segments.map((segment) => {
              const length = total ? (segment.value / total) * CIRCUMFERENCE : 0
              const circle = (
                <circle
                  key={segment.label}
                  cx="50"
                  cy="50"
                  r={RADIUS}
                  fill="none"
                  strokeWidth="12"
                  className={COLORS[segment.color].stroke}
                  strokeDasharray={`${length} ${CIRCUMFERENCE - length}`}
                  strokeDashoffset={-offset}
                  transform="rotate(-90 50 50)"
                />
              )
              offset += length
              return circle
            })}
            <text
              x="50"
              y="50"
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-slate-900 text-[18px] font-semibold"
            >
              {percent}%
            </text>
          </svg>

          <ul className="min-w-0 flex-1 space-y-1.5 text-sm">
            {segments.map((segment) => (
              <li key={segment.label} className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${COLORS[segment.color].dot}`} />
                <span className="text-slate-600">{segment.label}</span>
                <span className="ml-auto font-medium text-slate-900">{segment.value}</span>
              </li>
            ))}
          </ul>
        </div>

        {details.length > 0 && (
          <dl className="mt-5 space-y-3 border-t border-slate-100 pt-4 text-sm">
            {details.map((item) => (
              <div key={item.label}>
                <dt className="text-xs text-slate-500">{item.label}</dt>
                <dd className="mt-0.5 text-slate-900">{item.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </aside>
  )
}