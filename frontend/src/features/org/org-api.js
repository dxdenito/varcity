import { api } from '../../lib/api'

const BASE = '/api/v1/org'

export async function loadStructure() {
  const [types, nodes] = await Promise.all([api(`${BASE}/node-types`), api(`${BASE}/nodes`)])
  return { types, nodes }
}

export const initializeStructure = (template, institutionCode) =>
  api(`${BASE}/initialize`, {
    method: 'POST',
    body: { template, institution_code: institutionCode },
  })

export const createNode = (body) => api(`${BASE}/nodes`, { method: 'POST', body })
export const updateNode = (id, body) => api(`${BASE}/nodes/${id}`, { method: 'PATCH', body })
export const moveNode = (id, newParentId) =>
  api(`${BASE}/nodes/${id}/move`, { method: 'POST', body: { new_parent_id: newParentId } })
export const archiveNode = (id) => api(`${BASE}/nodes/${id}/archive`, { method: 'POST' })
export const unarchiveNode = (id) => api(`${BASE}/nodes/${id}/unarchive`, { method: 'POST' })
export const deleteNode = (id) => api(`${BASE}/nodes/${id}`, { method: 'DELETE' })
function upload(path, file) {
  const body = new FormData()
  body.append('file', file)
  return api(path, { method: 'POST', body })
}

export const previewImport = (nodeId, file) => upload(`${BASE}/nodes/${nodeId}/import/preview`, file)
export const importFile = (nodeId, file) => upload(`${BASE}/nodes/${nodeId}/import`, file)
