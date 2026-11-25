import { api } from '../../lib/api'

const BASE = '/api/v1/admin'

export function listUsers({ q, limit, offset }) {
  const params = new URLSearchParams({ limit, offset })
  if (q) params.set('q', q)
  return api(`${BASE}/users?${params}`)
}

export const getUser = (id) => api(`${BASE}/users/${id}`)
export const unlockUser = (id) => api(`${BASE}/users/${id}/unlock`, { method: 'POST' })
export const listNodes = () => api('/api/v1/org/nodes')

export const assignRole = (userId, roleId, nodeId) =>
  api(`${BASE}/users/${userId}/roles`, {
    method: 'POST',
    body: { role_id: roleId, node_id: nodeId },
  })

export const unassignRole = (userId, assignmentId) =>
  api(`${BASE}/users/${userId}/roles/${assignmentId}`, { method: 'DELETE' })

export const getPermissionTree = () => api(`${BASE}/permission-tree`)
export const listRoles = () => api(`${BASE}/roles`)
export const getRole = (id) => api(`${BASE}/roles/${id}`)
export const createRole = (body) => api(`${BASE}/roles`, { method: 'POST', body })
export const updateRole = (id, body) => api(`${BASE}/roles/${id}`, { method: 'PUT', body })
export const duplicateRole = (id, name) =>
  api(`${BASE}/roles/${id}/duplicate`, { method: 'POST', body: { name } })
export const deleteRole = (id) => api(`${BASE}/roles/${id}`, { method: 'DELETE' })