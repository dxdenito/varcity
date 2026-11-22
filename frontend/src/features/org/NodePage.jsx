import { Link } from 'react-router-dom'
import { ChevronRight, Network } from 'lucide-react'

import PageHeader from '../../components/ui/PageHeader'
import ChildrenSection from './ChildrenSection'
import DetailsSection from './DetailsSection'
import ManageSection from './ManageSection'
import { ancestorsOf } from './tree'
import ImportExportSection from './ImportExportSection'

export default function NodePage({ node, ctx }) {
  const type = ctx.typeById.get(node.type_id)
  const trail = ancestorsOf(ctx.index, node)

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <nav aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1 text-sm text-slate-500">
          {trail.map((item, position) => (
            <li key={item.id} className="flex items-center gap-1">
              {position > 0 && <ChevronRight size={14} aria-hidden="true" />}
              {item.id === node.id ? (
                <span className="font-medium text-slate-900" aria-current="page">
                  {item.name}
                </span>
              ) : (
                <Link
                  to={item.parent_id ? `/settings/organization/${item.id}` : '/settings/organization'}
                  className="hover:text-brand-700 hover:underline"
                >
                  {item.name}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </nav>

      <PageHeader
        icon={Network}
        title={node.name}
        subtitle={`${type?.name ?? ''}${node.code ? ` · ${node.code}` : ''}`}
        actions={
          node.status === 'archived' && (
            <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700">
              Archived
            </span>
          )
        }
      />

      <ChildrenSection node={node} ctx={ctx} />
      <ImportExportSection node={node} ctx={ctx} />
      <DetailsSection node={node} ctx={ctx} />
      {ctx.canEdit && <ManageSection node={node} ctx={ctx} />}
    </div>
  )
}