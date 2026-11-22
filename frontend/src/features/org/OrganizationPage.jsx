import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Network } from 'lucide-react'

import { useAuth } from '../../auth/auth-context'
import PageHeader from '../../components/ui/PageHeader'
import InitializePanel from './InitializePanel'
import NodePage from './NodePage'
import { loadStructure } from './org-api'
import { buildIndex } from './tree'

export default function OrganizationPage() {
  const { nodeId } = useParams()
  const { user } = useAuth()
  const canEdit = user.is_superuser

  const [data, setData] = useState(null)
  const [loadError, setLoadError] = useState(null)

  const reload = useCallback(async () => {
    try {
      setData(await loadStructure())
      setLoadError(null)
    } catch (err) {
      setLoadError(err.message)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const index = useMemo(() => buildIndex(data?.nodes ?? []), [data])
  const typeById = useMemo(
    () => new Map((data?.types ?? []).map((type) => [type.id, type])),
    [data],
  )

  if (loadError) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {loadError}
      </p>
    )
  }
  if (!data) return <div aria-busy="true" />

  if (data.types.length === 0) {
    return (
      <div className="mx-auto max-w-4xl space-y-5">
        <PageHeader
          icon={Network}
          title="Organization"
          subtitle="The structure of your university"
        />
        {canEdit ? (
          <InitializePanel onDone={reload} />
        ) : (
          <p className="rounded-xl bg-white p-6 text-sm text-slate-600">
            The organization structure has not been set up yet. Ask a system administrator.
          </p>
        )}
      </div>
    )
  }

  const node = nodeId ? index.byId.get(nodeId) : index.roots[0]
  if (!node) {
    return (
      <div className="mx-auto max-w-4xl rounded-xl bg-white p-6 text-sm text-slate-600">
        That entry no longer exists.{' '}
        <Link to="/settings/organization" className="text-brand-700 underline">
          Back to the university
        </Link>
      </div>
    )
  }

  const ctx = { types: data.types, nodes: data.nodes, index, typeById, canEdit, reload }
  return <NodePage key={node.id} node={node} ctx={ctx} />
}