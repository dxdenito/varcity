import { api } from '../../lib/api'

const BASE = '/api/v1/admin'

export function listUsers({ q, limit, offset }) {
  const params = new URLSearchParams({ limit, offset })
  if (q) params.set('q', q)
  return api(`${BASE}/users?${params}`)
}

export const getUser = (id) => api(`${BASE}/users/${id}`)
export const unlockUser = (id) => api(`${BASE}/users/${id}/unlock`, { method: 'POST' })
export const listRoles = () => api(`${BASE}/roles`)
export const listNodes = () => api('/api/v1/org/nodes')

export const assignRole = (userId, roleId, nodeId) =>
  api(`${BASE}/users/${userId}/roles`, {
    method: 'POST',
    body: { role_id: roleId, node_id: nodeId },
  })

export const unassignRole = (userId, assignmentId) =>
  api(`${BASE}/users/${userId}/roles/${assignmentId}`, { method: 'DELETE' })