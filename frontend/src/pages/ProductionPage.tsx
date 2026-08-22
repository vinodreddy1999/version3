import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { inventoryApi, productionApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { usePagingOffset } from '../lib/usePagingOffset'
import { ClipboardList, Factory } from 'lucide-react'
import { Alert, Badge, Button, Card, EmptyState, ExportButton, Field, Input, PageHeader, Pager, Select, Table } from '../components/ui'

const ORDERS_PAGE_SIZE = 20

export function ProductionPage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()
  const [ordersOffset, setOrdersOffset] = usePagingOffset(selectedPlantId)

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: boms = [] } = useQuery({ queryKey: ['boms'], queryFn: productionApi.listBoms })
  const { data: ordersPage } = useQuery({
    queryKey: ['production-orders', selectedPlantId, ordersOffset],
    queryFn: () => productionApi.listOrders(selectedPlantId ?? undefined, { limit: ORDERS_PAGE_SIZE, offset: ordersOffset }),
  })
  const orders = ordersPage?.items ?? []

  const [bomForm, setBomForm] = useState({
    output_item_id: '',
    name: '',
    components: [{ component_item_id: '', quantity_per_unit: '' }],
  })
  const [orderForm, setOrderForm] = useState({ bom_id: '', quantity_planned: '' })
  const [completeQuantities, setCompleteQuantities] = useState<Record<string, string>>({})
  const [bomError, setBomError] = useState<string | null>(null)

  const createBom = useMutation({
    mutationFn: () =>
      productionApi.createBom({
        output_item_id: bomForm.output_item_id,
        name: bomForm.name,
        components: bomForm.components.filter((c) => c.component_item_id && c.quantity_per_unit),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boms'] })
      setBomForm({ output_item_id: '', name: '', components: [{ component_item_id: '', quantity_per_unit: '' }] })
      setBomError(null)
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setBomError(message ?? 'Could not create BOM.')
    },
  })

  const createOrder = useMutation({
    mutationFn: () => productionApi.createOrder({ plant_id: selectedPlantId!, ...orderForm }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['production-orders'] })
      setOrderForm({ bom_id: '', quantity_planned: '' })
    },
  })

  const completeOrder = useMutation({
    mutationFn: ({ id, quantity }: { id: string; quantity: string }) => productionApi.completeOrder(id, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['production-orders'] })
      queryClient.invalidateQueries({ queryKey: ['balances'] })
    },
  })

  const statusTone = { planned: 'slate', in_progress: 'blue', completed: 'green', cancelled: 'red' } as const

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Production" description="Bills of material and production orders." />

      <Card title="Bills of Material" icon={<ClipboardList className="h-4 w-4" />}>
        {bomError && <Alert onDismiss={() => setBomError(null)}>{bomError}</Alert>}
        <form
          className="mb-4 flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            createBom.mutate()
          }}
        >
          <div className="flex flex-wrap items-end gap-2">
            <Field label="BOM name">
              <Input required value={bomForm.name} onChange={(e) => setBomForm({ ...bomForm, name: e.target.value })} className="w-40" />
            </Field>
            <Field label="Output item">
              <Select
                required
                value={bomForm.output_item_id}
                onChange={(e) => setBomForm({ ...bomForm, output_item_id: e.target.value })}
                className="w-48"
              >
                <option value="">Select item…</option>
                {items.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.sku} — {i.name}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <p className="mt-2 text-xs font-semibold text-slate-500">Components</p>
          {bomForm.components.map((comp, idx) => (
            <div key={idx} className="flex items-end gap-2">
              <Select
                value={comp.component_item_id}
                onChange={(e) => {
                  const next = [...bomForm.components]
                  next[idx] = { ...next[idx], component_item_id: e.target.value }
                  setBomForm({ ...bomForm, components: next })
                }}
                className="w-48"
              >
                <option value="">Select component…</option>
                {items.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.sku} — {i.name}
                  </option>
                ))}
              </Select>
              <Input
                type="number"
                step="any"
                placeholder="Qty per unit"
                value={comp.quantity_per_unit}
                onChange={(e) => {
                  const next = [...bomForm.components]
                  next[idx] = { ...next[idx], quantity_per_unit: e.target.value }
                  setBomForm({ ...bomForm, components: next })
                }}
                className="w-32"
              />
            </div>
          ))}
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                setBomForm({ ...bomForm, components: [...bomForm.components, { component_item_id: '', quantity_per_unit: '' }] })
              }
            >
              + Add component
            </Button>
            <Button type="submit" disabled={createBom.isPending}>
              Create BOM
            </Button>
          </div>
        </form>

        {boms.length === 0 ? (
          <EmptyState message="No BOMs yet." />
        ) : (
          <Table headers={['Name', 'Output item', 'Components']}>
            {boms.map((b) => (
              <tr key={b.id}>
                <td className="px-3 py-2">{b.name}</td>
                <td className="px-3 py-2 font-mono text-xs">{items.find((i) => i.id === b.output_item_id)?.sku}</td>
                <td className="px-3 py-2 text-slate-500">
                  {b.components.map((c) => `${c.component_sku} x${c.quantity_per_unit}`).join(', ')}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card
        title="Production orders"
        icon={<Factory className="h-4 w-4" />}
        actions={<ExportButton onExport={() => productionApi.exportOrders(selectedPlantId ?? undefined)} />}
      >
        {!selectedPlantId ? (
          <EmptyState message="Select a plant to manage production orders." />
        ) : (
          <>
            <form
              className="mb-4 flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                createOrder.mutate()
              }}
            >
              <Field label="BOM">
                <Select required value={orderForm.bom_id} onChange={(e) => setOrderForm({ ...orderForm, bom_id: e.target.value })} className="w-56">
                  <option value="">Select BOM…</option>
                  {boms.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Quantity planned">
                <Input
                  required
                  type="number"
                  step="any"
                  value={orderForm.quantity_planned}
                  onChange={(e) => setOrderForm({ ...orderForm, quantity_planned: e.target.value })}
                  className="w-28"
                />
              </Field>
              <Button type="submit" disabled={createOrder.isPending}>
                Create order
              </Button>
            </form>

            {orders.length === 0 ? (
              <EmptyState message="No production orders yet." />
            ) : (
              <>
                <Table headers={['BOM', 'Planned', 'Completed', 'Status', 'Complete']}>
                  {orders.map((o) => (
                    <tr key={o.id}>
                      <td className="px-3 py-2">{boms.find((b) => b.id === o.bom_id)?.name ?? o.bom_id}</td>
                      <td className="px-3 py-2">{o.quantity_planned}</td>
                      <td className="px-3 py-2">{o.quantity_completed}</td>
                      <td className="px-3 py-2">
                        <Badge tone={statusTone[o.status]}>{o.status.replace('_', ' ')}</Badge>
                      </td>
                      <td className="px-3 py-2">
                        {o.status === 'planned' || o.status === 'in_progress' ? (
                          <div className="flex items-center gap-1">
                            <Input
                              type="number"
                              step="any"
                              placeholder="Qty"
                              value={completeQuantities[o.id] ?? ''}
                              onChange={(e) => setCompleteQuantities({ ...completeQuantities, [o.id]: e.target.value })}
                              className="w-20"
                            />
                            <Button
                              variant="secondary"
                              onClick={() => completeOrder.mutate({ id: o.id, quantity: completeQuantities[o.id] ?? '0' })}
                              disabled={completeOrder.isPending}
                            >
                              Complete
                            </Button>
                          </div>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </Table>
                <Pager
                  offset={ordersOffset}
                  limit={ORDERS_PAGE_SIZE}
                  total={ordersPage?.total ?? 0}
                  onOffsetChange={setOrdersOffset}
                />
              </>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
