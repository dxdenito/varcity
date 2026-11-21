// Used only for live previews. The server remains the authority on the real palette.
function channel(value) {
  const scaled = value / 255
  return scaled <= 0.03928 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4
}

function luminance(hex) {
  const value = hex.replace('#', '')
  const r = parseInt(value.slice(0, 2), 16)
  const g = parseInt(value.slice(2, 4), 16)
  const b = parseInt(value.slice(4, 6), 16)
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}

const DARK_TEXT = '#111827'
const LIGHT_TEXT = '#ffffff'

export function readableTextColor(background) {
  const l = luminance(background)
  const contrastWithWhite = 1.05 / (l + 0.05)
  const contrastWithDark = (l + 0.05) / (luminance(DARK_TEXT) + 0.05)
  return contrastWithWhite >= contrastWithDark ? LIGHT_TEXT : DARK_TEXT
}