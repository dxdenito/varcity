// The CSRF token lives in memory only (never in localStorage or cookies).
let csrfToken = null

export function setCsrfToken(token) {
  csrfToken = token
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

// FastAPI returns { detail: "text" } or, for validation errors, a list of messages.
function errorMessage(data) {
  if (!data || !data.detail) return null
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) return data.detail.map((item) => item.msg).join(' ')
  return null
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method !== 'GET' && csrfToken) headers['X-CSRF-Token'] = csrfToken

  let response
  try {
    response = await fetch(path, {
      method,
      headers,
      credentials: 'same-origin', // send the session cookie
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.')
  }

  if (response.status === 204) return null

  let data = null
  try {
    data = await response.json()
  } catch {
    // no JSON body
  }

  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(data) ?? `Request failed (${response.status})`)
  }
  return data
}