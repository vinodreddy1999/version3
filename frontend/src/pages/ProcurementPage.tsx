import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { inventoryApi, procurementApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { usePagingOffset } from '../lib/usePagingOffset'
import { ShoppingCart, Truck } from 'lucide-react'
import { AttachmentsPanel } from '../components/AttachmentsPanel'
import { Badge, Button, Card, EmptyState, ExportButton, Field, Input, PageHeader, Pager, Select, Table } from '../components/ui'

const ORDERS_PAGE_SIZE = 20

export function ProcurementPage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()
  const [ordersOffset, setOrdersOffset] = usePagingOffset(selectedPlantId)

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: suppliers = [] } = useQuery({ queryKey: ['suppliers'], queryFn: procurementApi.listSuppliers })
  const { data: ordersPage } = useQuery({
    queryKey: ['purchase-orders', selectedPlantId, ordersOffset],
    queryFn: () => procurementApi.listOrders(selectedPlantId ?? undefined, { limit: ORDERS_PAGE_SIZE, offset: ordersOffset }),
  })
  const orders = ordersPage?.items ?? []

  const [supplierForm, setSupplierForm] = useState({ name: '', code: '' })
  const [orderForm, setOrderForm] = useState({ supplier_id: '', item_id: '', quantity_ordered: '', unit_price: '' })
  const [receiveQuantities, setReceiveQuantities] = useState<Record<string, string>>({})

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })
    queryClient.invalidateQueries({ queryKey: ['balances'] })
  }

  const createSupplier = useMutation({
    mutationFn: procurementApi.createSupplier,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] })
      setSupplierForm({ name: '', code: '' })
    },
  })

  const createOrder = useMutation({
    mutationFn: () =>
      procurementApi.createOrder({
        plant_id: selectedPlantId!,
        supplier_id: orderForm.supplier_id,
        lines: [{ item_id: orderForm.item_id, quantity_ordered: orderForm.quantity_ordered, unit_price: orderForm.unit_price || undefined }],
      }),
    onSuccess: () => {
      invalidate()
      setOrderForm({ supplier_id: '', item_id: '', quantity_ordered: '', unit_price: '' })
    },
  })

  const submitOrder = useMutation({ mutationFn: procurementApi.submitOrder, onSuccess: invalidate })
  const receiveLine = useMutation({
    mutationFn: ({ orderId, lineId, quantity }: { orderId: string; lineId: string; quantity: string }) =>
      procurementApi.receiveLine(orderId, lineId, quantity),
    onSuccess: invalidate,
  })

  const statusTone = {
    draft: 'slate',
    submitted: 'blue',
    partially_received: 'amber',
    received: 'green',
    cancelled: 'red',
  } as const

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Procurement" description="Suppliers and purchase orders." />

      <Card
        title="Suppliers"
        icon={<Truck className="h-4 w-4" />}
        actions={
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              createSupplier.mutate(supplierForm)
            }}
          >
            <Input placeholder="Name" required value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} className="w-40" />
            <Input placeholder="Code" required value={supplierForm.code} onChange={(e) => setSupplierForm({ ...supplierForm, code: e.target.value })} className="w-28" />
            <Button type="submit" disabled={createSupplier.isPending}>
              Add
            </Button>
          </form>
        }
      >
        {suppliers.length === 0 ? (
          <EmptyState message="No suppliers yet." />
        ) : (
          <Table headers={['Name', 'Code']}>
            {suppliers.map((s) => (
              <tr key={s.id}>
                <td className="px-3 py-2">{s.name}</td>
                <td className="px-3 py-2 text-slate-500">{s.code}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card
        title="Purchase orders"
        icon={<ShoppingCart className="h-4 w-4" />}
        actions={<ExportButton onExport={() => procurementApi.exportOrders(selectedPlantId ?? undefined)} />}
      >
        {!selectedPlantId ? (
          <EmptyState message="Select a plant to manage purchase orders." />
        ) : (
          <>
            <form
              className="mb-4 flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                createOrder.mutate()
              }}
            >
              <Field label="Supplier">
                <Select required value={orderForm.supplier_id} onChange={(e) => setOrderForm({ ...orderForm, supplier_id: e.target.value })} className="w-40">
                  <option value="">Select…</option>
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Item">
                <Select required value={orderForm.item_id} onChange={(e) => setOrderForm({ ...orderForm, item_id: e.target.value })} className="w-40">
                  <option value="">Select…</option>
                  {items.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.sku}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Qty ordered">
                <Input required type="number" step="any" value={orderForm.quantity_ordered} onChange={(e) => setOrderForm({ ...orderForm, quantity_ordered: e.target.value })} className="w-24" />
              </Field>
              <Field label="Unit price">
                <Input type="number" step="any" value={orderForm.unit_price} onChange={(e) => setOrderForm({ ...orderForm, unit_price: e.target.value })} className="w-24" />
              </Field>
              <Button type="submit" disabled={createOrder.isPending}>
                Create PO
              </Button>
            </form>

            {orders.length === 0 ? (
              <EmptyState message="No purchase orders yet." />
            ) : (
              <>
              <div className="flex flex-col gap-3">
                {orders.map((o) => (
                  <div key={o.id} className="rounded-md border border-slate-200 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{suppliers.find((s) => s.id === o.supplier_id)?.name}</span>
                        <Badge tone={statusTone[o.status]}>{o.status.replace('_', ' ')}</Badge>
                      </div>
                      {o.status === 'draft' && (
                        <Button variant="secondary" onClick={() => submitOrder.mutate(o.id)} disabled={submitOrder.isPending}>
                          Submit
                        </Button>
                      )}
                    </div>
                    <Table headers={['Item', 'Ordered', 'Received', 'Receive qty', '']}>
                      {o.lines.map((line) => (
                        <tr key={line.id}>
                          <td className="px-3 py-2 font-mono text-xs">{line.item_sku}</td>
                          <td className="px-3 py-2">{line.quantity_ordered}</td>
                          <td className="px-3 py-2">{line.quantity_received}</td>
                          <td className="px-3 py-2">
                            {(o.status === 'submitted' || o.status === 'partially_received') && (
                              <Input
                                type="number"
                                step="any"
                                placeholder="Qty"
                                value={receiveQuantities[line.id] ?? ''}
                                onChange={(e) => setReceiveQuantities({ ...receiveQuantities, [line.id]: e.target.value })}
                                className="w-20"
                              />
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {(o.status === 'submitted' || o.status === 'partially_received') && (
                              <Button
                                variant="secondary"
                                onClick={() =>
                                  receiveLine.mutate({ orderId: o.id, lineId: line.id, quantity: receiveQuantities[line.id] ?? '0' })
                                }
                                disabled={receiveLine.isPending}
                              >
                                Receive
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </Table>
                    <AttachmentsPanel entityType="purchase_order" entityId={o.id} />
                  </div>
                ))}
              </div>
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
