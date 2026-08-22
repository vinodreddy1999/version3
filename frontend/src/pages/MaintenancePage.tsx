import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { maintenanceApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { usePagingOffset } from '../lib/usePagingOffset'
import { HardHat, Wrench } from 'lucide-react'
import { Badge, Button, Card, EmptyState, Field, Input, PageHeader, Pager, Select, Table } from '../components/ui'

const WORK_ORDERS_PAGE_SIZE = 20

export function MaintenancePage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()
  const [workOrdersOffset, setWorkOrdersOffset] = usePagingOffset(selectedPlantId)

  const { data: assets = [] } = useQuery({
    queryKey: ['assets', selectedPlantId],
    queryFn: () => maintenanceApi.listAssets(selectedPlantId ?? undefined),
  })
  const { data: workOrdersPage } = useQuery({
    queryKey: ['work-orders', selectedPlantId, workOrdersOffset],
    queryFn: () =>
      maintenanceApi.listWorkOrders(selectedPlantId ?? undefined, {
        limit: WORK_ORDERS_PAGE_SIZE,
        offset: workOrdersOffset,
      }),
  })
  const workOrders = workOrdersPage?.items ?? []

  const [assetForm, setAssetForm] = useState({ name: '', code: '' })
  const [woForm, setWoForm] = useState({ asset_id: '', work_order_type: 'corrective', description: '' })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['assets'] })
    queryClient.invalidateQueries({ queryKey: ['work-orders'] })
  }

  const createAsset = useMutation({
    mutationFn: () => maintenanceApi.createAsset({ plant_id: selectedPlantId!, ...assetForm }),
    onSuccess: () => {
      invalidate()
      setAssetForm({ name: '', code: '' })
    },
  })

  const createWorkOrder = useMutation({
    mutationFn: () => maintenanceApi.createWorkOrder({ plant_id: selectedPlantId!, ...woForm }),
    onSuccess: () => {
      invalidate()
      setWoForm({ asset_id: '', work_order_type: 'corrective', description: '' })
    },
  })

  const startWo = useMutation({ mutationFn: maintenanceApi.startWorkOrder, onSuccess: invalidate })
  const completeWo = useMutation({ mutationFn: maintenanceApi.completeWorkOrder, onSuccess: invalidate })
  const cancelWo = useMutation({ mutationFn: maintenanceApi.cancelWorkOrder, onSuccess: invalidate })

  const assetTone = { operational: 'green', down: 'red', maintenance: 'amber' } as const
  const woTone = { open: 'slate', in_progress: 'blue', completed: 'green', cancelled: 'red' } as const

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Maintenance" description="Assets and the maintenance work order lifecycle." />

      {!selectedPlantId ? (
        <EmptyState message="Select a plant to manage assets and work orders." />
      ) : (
        <>
          <Card
            title="Assets"
            icon={<HardHat className="h-4 w-4" />}
            actions={
              <form
                className="flex items-end gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  createAsset.mutate()
                }}
              >
                <Input placeholder="Name" required value={assetForm.name} onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })} className="w-36" />
                <Input placeholder="Code" required value={assetForm.code} onChange={(e) => setAssetForm({ ...assetForm, code: e.target.value })} className="w-24" />
                <Button type="submit" disabled={createAsset.isPending}>
                  Add
                </Button>
              </form>
            }
          >
            {assets.length === 0 ? (
              <EmptyState message="No assets yet." />
            ) : (
              <Table headers={['Name', 'Code', 'Status']}>
                {assets.map((a) => (
                  <tr key={a.id}>
                    <td className="px-3 py-2">{a.name}</td>
                    <td className="px-3 py-2 text-slate-500">{a.code}</td>
                    <td className="px-3 py-2">
                      <Badge tone={assetTone[a.status]}>{a.status}</Badge>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>

          <Card title="Work orders" icon={<Wrench className="h-4 w-4" />}>
            <form
              className="mb-4 flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                createWorkOrder.mutate()
              }}
            >
              <Field label="Asset">
                <Select required value={woForm.asset_id} onChange={(e) => setWoForm({ ...woForm, asset_id: e.target.value })} className="w-40">
                  <option value="">Select…</option>
                  {assets.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Type">
                <Select value={woForm.work_order_type} onChange={(e) => setWoForm({ ...woForm, work_order_type: e.target.value })} className="w-36">
                  <option value="corrective">Corrective</option>
                  <option value="preventive">Preventive</option>
                  <option value="inspection">Inspection</option>
                </Select>
              </Field>
              <Field label="Description">
                <Input value={woForm.description} onChange={(e) => setWoForm({ ...woForm, description: e.target.value })} className="w-48" />
              </Field>
              <Button type="submit" disabled={createWorkOrder.isPending}>
                Create
              </Button>
            </form>

            {workOrders.length === 0 ? (
              <EmptyState message="No work orders yet." />
            ) : (
              <>
              <Table headers={['Asset', 'Type', 'Status', 'Actions']}>
                {workOrders.map((wo) => (
                  <tr key={wo.id}>
                    <td className="px-3 py-2">{assets.find((a) => a.id === wo.asset_id)?.name}</td>
                    <td className="px-3 py-2 text-slate-500">{wo.work_order_type}</td>
                    <td className="px-3 py-2">
                      <Badge tone={woTone[wo.status]}>{wo.status.replace('_', ' ')}</Badge>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1">
                        {wo.status === 'open' && (
                          <>
                            <Button variant="secondary" onClick={() => startWo.mutate(wo.id)}>
                              Start
                            </Button>
                            <Button variant="danger" onClick={() => cancelWo.mutate(wo.id)}>
                              Cancel
                            </Button>
                          </>
                        )}
                        {wo.status === 'in_progress' && (
                          <>
                            <Button variant="secondary" onClick={() => completeWo.mutate(wo.id)}>
                              Complete
                            </Button>
                            <Button variant="danger" onClick={() => cancelWo.mutate(wo.id)}>
                              Cancel
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </Table>
              <Pager
                offset={workOrdersOffset}
                limit={WORK_ORDERS_PAGE_SIZE}
                total={workOrdersPage?.total ?? 0}
                onOffsetChange={setWorkOrdersOffset}
              />
              </>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
