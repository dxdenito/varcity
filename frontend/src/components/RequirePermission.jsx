import { Lock } from 'lucide-react'

import { usePermissions } from '../auth/usePermissions'

export default function RequirePermission({ perm, children }) {
  const { canAnywhere } = usePermissions()

  if ([].concat(perm).some(canAnywhere)) return children

  return (
    <div className="mx-auto mt-10 max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center">
      <Lock size={28} className="mx-auto text-slate-400" aria-hidden="true" />
      <h1 className="mt-3 text-lg font-semibold text-slate-900">No access</h1>
      <p className="mt-1 text-sm text-slate-500">
        You do not have permission to open this page. Ask an administrator if you need it.
      </p>
    </div>
  )
}