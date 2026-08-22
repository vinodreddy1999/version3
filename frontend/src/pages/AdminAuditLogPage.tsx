import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { History } from 'lucide-react'
import { adminApi } from '../api/endpoints'
import { Badge, Card, EmptyState, PageHeader, Pager, Table } from '../components/ui'

const PAGE_SIZE = 25

function actionTone(action: string): 'red' | 'amber' | 'blue' | 'green' | 'slate' {
  if (action.endsWith('.deleted')) return 'red'
  if (action.includes('deactivat') || action === 'role.updated' || action === 'user.updated') return 'amber'
  if (action.endsWith('.created') || action === 'tenant.registered') return 'green'
  if (action === 'user.login') return 'blue'
  return 'slate'
}

export function AdminAuditLogPage() {
  const [offset, setOffset] = useState(0)
  const { data } = useQuery({
    queryKey: ['audit-log', offset],
    queryFn: () => adminApi.listAuditLog({ limit: PAGE_SIZE, offset }),
  })
  const entries = data?.items ?? []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Audit log" description="Who changed what, and when — account and access changes only." />

      <Card icon={<History className="h-4 w-4" />}>
        {entries.length === 0 ? (
          <EmptyState message="Nothing logged yet." />
        ) : (
          <>
            <Table headers={['When', 'Actor', 'Action', 'Details']}>
              {entries.map((e) => (
                <tr key={e.id}>
                  <td className="whitespace-nowrap px-3 py-2 text-slate-500">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">{e.actor_email ?? <span className="text-slate-400">system</span>}</td>
                  <td className="px-3 py-2">
                    <Badge tone={actionTone(e.action)}>{e.action}</Badge>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{e.summary}</td>
                </tr>
              ))}
            </Table>
            <Pager offset={offset} limit={PAGE_SIZE} total={data?.total ?? 0} onOffsetChange={setOffset} />
          </>
        )}
      </Card>
    </div>
  )
}
