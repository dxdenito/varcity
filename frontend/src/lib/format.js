export const DATE_FORMATS = ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD', 'D MMM YYYY']

export function formatDate(date, format) {
  const day = date.getDate()
  const month = date.getMonth() + 1
  const year = date.getFullYear()
  const two = (value) => String(value).padStart(2, '0')

  switch (format) {
    case 'MM/DD/YYYY':
      return `${two(month)}/${two(day)}/${year}`
    case 'YYYY-MM-DD':
      return `${year}-${two(month)}-${two(day)}`
    case 'D MMM YYYY':
      return `${day} ${date.toLocaleString('en-GB', { month: 'short' })} ${year}`
    default:
      return `${two(day)}/${two(month)}/${year}`
  }
}