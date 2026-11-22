export default function PageHeader({ icon: Icon, title, subtitle, actions }) {
  return (
    <header className="flex flex-wrap items-center gap-4">
      {Icon && (
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
          <Icon size={22} aria-hidden="true" />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  )
}