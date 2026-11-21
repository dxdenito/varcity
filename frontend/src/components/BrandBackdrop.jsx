const GRID_LINE = 'color-mix(in srgb, var(--on-sidebar) 7%, transparent)'

export default function BrandBackdrop({ children }) {
  return (
    <div
      className="relative min-h-screen overflow-hidden text-on-sidebar"
      style={{
        background:
          'linear-gradient(135deg, var(--sidebar) 0%, color-mix(in srgb, var(--sidebar) 75%, var(--brand-600)) 100%)',
      }}
    >
      <div className="pointer-events-none absolute -left-32 -top-32 h-[30rem] w-[30rem] animate-float rounded-full bg-brand-400/30 blur-3xl motion-reduce:animate-none" />
      <div className="pointer-events-none absolute -bottom-40 right-0 h-[34rem] w-[34rem] animate-float rounded-full bg-brand-600/40 blur-3xl [animation-delay:-7s] motion-reduce:animate-none" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: `linear-gradient(${GRID_LINE} 1px, transparent 1px), linear-gradient(90deg, ${GRID_LINE} 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }}
      />
      <svg
        className="pointer-events-none absolute -bottom-24 -left-24 h-[28rem] w-[28rem] opacity-20"
        viewBox="0 0 200 200"
        fill="none"
        stroke="currentColor"
        aria-hidden="true"
      >
        <circle cx="100" cy="100" r="30" />
        <circle cx="100" cy="100" r="55" />
        <circle cx="100" cy="100" r="80" />
        <circle cx="100" cy="100" r="105" />
      </svg>
      <div className="relative">{children}</div>
    </div>
  )
}