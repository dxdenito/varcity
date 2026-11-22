export function buildIndex(nodes) {
  const byId = new Map(nodes.map((node) => [node.id, node]))
  const childrenOf = new Map()

  for (const node of nodes) {
    if (!node.parent_id) continue
    if (!childrenOf.has(node.parent_id)) childrenOf.set(node.parent_id, [])
    childrenOf.get(node.parent_id).push(node)
  }
  for (const list of childrenOf.values()) {
    list.sort((a, b) => a.name.localeCompare(b.name))
  }

  return { byId, childrenOf, roots: nodes.filter((node) => !node.parent_id) }
}

export function descendantIds(index, id) {
  const result = new Set([id])
  const stack = [id]
  while (stack.length) {
    for (const child of index.childrenOf.get(stack.pop()) ?? []) {
      result.add(child.id)
      stack.push(child.id)
    }
  }
  return result
}

export function pathLabel(index, node) {
  const names = []
  for (let current = node; current; current = index.byId.get(current.parent_id)) {
    names.unshift(current.name)
  }
  return names.join(' › ')
}

export function ancestorsOf(index, node) {
  const trail = []
  for (let current = node; current; current = index.byId.get(current.parent_id)) {
    trail.unshift(current)
  }
  return trail
}