import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { inventoryApi, qualityApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { usePagingOffset } from '../lib/usePagingOffset'
import { ClipboardCheck } from 'lucide-react'
import { AttachmentsPanel } from '../components/AttachmentsPanel'
import { Badge, Button, Card, EmptyState, Field, Input, PageHeader, Pager, Select, Table } from '../components/ui'

const INSPECTIONS_PAGE_SIZE = 20

export function QualityPage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()
  const [inspectionsOffset, setInspectionsOffset] = usePagingOffset(selectedPlantId)

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: inspectionsPage } = useQuery({
    queryKey: ['inspections', selectedPlantId, inspectionsOffset],
    queryFn: () =>
      qualityApi.listInspections(selectedPlantId ?? undefined, {
        limit: INSPECTIONS_PAGE_SIZE,
        offset: inspectionsOffset,
      }),
  })
  const inspections = inspectionsPage?.items ?? []

  const [form, setForm] = useState({
    item_id: '',
    inspected_quantity: '',
    defect_type: '',
    defect_severity: 'minor',
    defect_quantity: '',
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['inspections'] })

  const createInspection = useMutation({
    mutationFn: () =>
      qualityApi.createInspection({
        plant_id: selectedPlantId!,
        item_id: form.item_id,
        inspected_quantity: form.inspected_quantity,
        defects:
          form.defect_type && form.defect_quantity
            ? [{ defect_type: form.defect_type, severity: form.defect_severity, quantity: form.defect_quantity }]
            : [],
      }),
    onSuccess: () => {
      invalidate()
      setForm({ item_id: '', inspected_quantity: '', defect_type: '', defect_severity: 'minor', defect_quantity: '' })
    },
  })

  const resolveDefect = useMutation({ mutationFn: qualityApi.resolveDefect, onSuccess: invalidate })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Quality" description="Inspections and defect tracking." />

      {!selectedPlantId ? (
        <EmptyState message="Select a plant to log inspections." />
      ) : (
        <Card title="Inspections" icon={<ClipboardCheck className="h-4 w-4" />}>
          <form
            className="mb-4 flex flex-wrap items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              createInspection.mutate()
            }}
          >
            <Field label="Item">
              <Select required value={form.item_id} onChange={(e) => setForm({ ...form, item_id: e.target.value })} className="w-40">
                <option value="">Select…</option>
                {items.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.sku}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Inspected qty">
              <Input required type="number" step="any" value={form.inspected_quantity} onChange={(e) => setForm({ ...form, inspected_quantity: e.target.value })} className="w-24" />
            </Field>
            <Field label="Defect type (optional)">
              <Input value={form.defect_type} onChange={(e) => setForm({ ...form, defect_type: e.target.value })} className="w-32" placeholder="e.g. scratch" />
            </Field>
            <Field label="Severity">
              <Select value={form.defect_severity} onChange={(e) => setForm({ ...form, defect_severity: e.target.value })} className="w-28">
                <option value="minor">Minor</option>
                <option value="major">Major</option>
                <option value="critical">Critical</option>
              </Select>
            </Field>
            <Field label="Defect qty">
              <Input type="number" step="any" value={form.defect_quantity} onChange={(e) => setForm({ ...form, defect_quantity: e.target.value })} className="w-20" />
            </Field>
            <Button type="submit" disabled={createInspection.isPending}>
              Log inspection
            </Button>
          </form>

          {inspections.length === 0 ? (
            <EmptyState message="No inspections logged yet." />
          ) : (
            <>
            <div className="flex flex-col gap-3">
              {inspections.map((insp) => (
                <div key={insp.id} className="rounded-md border border-slate-200 p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="font-mono text-xs">{items.find((i) => i.id === insp.item_id)?.sku}</span>
                    <span className="text-sm text-slate-500">qty {insp.inspected_quantity}</span>
                    <Badge tone={insp.result === 'pass' ? 'green' : 'red'}>{insp.result}</Badge>
                  </div>
                  {insp.defects.length > 0 && (
                    <Table headers={['Defect', 'Severity', 'Qty', 'Status', '']}>
                      {insp.defects.map((d) => (
                        <tr key={d.id}>
                          <td className="px-3 py-2">{d.defect_type}</td>
                          <td className="px-3 py-2 text-slate-500">{d.severity}</td>
                          <td className="px-3 py-2">{d.quantity}</td>
                          <td className="px-3 py-2">
                            <Badge tone={d.status === 'open' ? 'amber' : 'green'}>{d.status}</Badge>
                          </td>
                          <td className="px-3 py-2">
                            {d.status === 'open' && (
                              <Button variant="secondary" onClick={() => resolveDefect.mutate(d.id)}>
                                Resolve
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </Table>
                  )}
                  <AttachmentsPanel entityType="inspection" entityId={insp.id} />
                </div>
              ))}
            </div>
            <Pager
              offset={inspectionsOffset}
              limit={INSPECTIONS_PAGE_SIZE}
              total={inspectionsPage?.total ?? 0}
              onOffsetChange={setInspectionsOffset}
            />
            </>
          )}
        </Card>
      )}
    </div>
  )
}
