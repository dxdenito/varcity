export const codesOf = (group) =>
  group.resources.flatMap((resource) => resource.permissions.map((p) => p.code))

export const allCodes = (tree) => tree.flatMap(codesOf)

export function riskByCode(tree) {
  return new Map(
    tree.flatMap((group) =>
      group.resources.flatMap((resource) => resource.permissions.map((p) => [p.code, p.risk])),
    ),
  )
}

// Choosing an action also chooses viewing; removing viewing removes the other actions.
export function applyToggle(tree, selected, codes, checked) {
  const next = new Set(selected)
  for (const code of codes) {
    if (checked) next.add(code)
    else next.delete(code)
  }
  for (const group of tree) {
    for (const resource of group.resources) {
      const view = resource.permissions.find((p) => p.action === 'view')
      if (!view) continue
      const others = resource.permissions.filter((p) => p !== view)
      if (checked && others.some((p) => next.has(p.code))) next.add(view.code)
      if (!checked && codes.includes(view.code)) others.forEach((p) => next.delete(p.code))
    }
  }
  return next
}