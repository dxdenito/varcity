function initials(name) {
  const words = name.split(/\s+/).filter(Boolean)
  if (words.length <= 1) return (words[0] ?? '?').slice(0, 2).toUpperCase()
  return words
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
}

export default function BrandLogo({ branding, size = 'h-12 w-12' }) {
  if (branding.logo_url) {
    return <img src={branding.logo_url} alt="" className={`${size} rounded object-contain`} />
  }
  return (
    <div
      className={`${size} flex items-center justify-center rounded-lg bg-brand-600 text-lg font-bold text-on-brand`}
    >
      {initials(branding.short_name)}
    </div>
  )
}