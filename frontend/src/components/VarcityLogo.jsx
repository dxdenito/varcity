export default function VarcityLogo({ size = 40, showWordmark = true }) {
  return (
    <div className="flex items-center gap-3">
      <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
        <defs>
          <linearGradient id="varcity-logo-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#60a5fa" />
            <stop offset="1" stopColor="#4f46e5" />
          </linearGradient>
        </defs>
        <rect width="48" height="48" rx="12" fill="url(#varcity-logo-gradient)" />
        <path
          d="M13 21l11 18 11-18"
          fill="none"
          stroke="#fff"
          strokeWidth="4.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M24 8l10 5-10 5-10-5z" fill="#fff" />
      </svg>
      {showWordmark && <span className="text-2xl font-semibold tracking-tight">Varcity</span>}
    </div>
  )
}