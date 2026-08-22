import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { inventoryApi, salesApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { ShoppingCart, Users } from 'lucide-react'
import { Alert, Badge, Button, Card, EmptyState, Field, Input, PageHeader, Select, Table } from '../components/ui'

export function SalesPage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: customers = [] } = useQuery({ queryKey: ['customers'], queryFn: salesApi.listCustomers })
  const { data: orders = [] } = useQuery({
    queryKey: ['sales-orders', selectedPlantId],
    queryFn: () => salesApi.listOrders(selectedPlantId ?? undefined),
  })

  const [customerForm, setCustomerForm] = useState({ name: '', code: '' })
  const [orderForm, setOrderForm] = useState({ customer_id: '', item_id: '', quantity_ordered: '', unit_price: '' })
  const [shipQuantities, setShipQuantities] = useState<Record<string, string>>({})
  const [shipError, setShipError] = useState<string | null>(null)

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['sales-orders'] })
    queryClient.invalidateQueries({ queryKey: ['balances'] })
  }

  const createCustomer = useMutation({
    mutationFn: salesApi.createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      setCustomerForm({ name: '', code: '' })
    },
  })

  const createOrder = useMutation({
    mutationFn: () =>
      salesApi.createOrder({
        plant_id: selectedPlantId!,
        customer_id: orderForm.customer_id,
        lines: [{ item_id: orderForm.item_id, quantity_ordered: orderForm.quantity_ordered, unit_price: orderForm.unit_price || undefined }],
      }),
    onSuccess: () => {
      invalidate()
      setOrderForm({ customer_id: '', item_id: '', quantity_ordered: '', unit_price: '' })
    },
  })

  const confirmOrder = useMutation({ mutationFn: salesApi.confirmOrder, onSuccess: invalidate })
  const shipLine = useMutation({
    mutationFn: ({ orderId, lineId, quantity }: { orderId: string; lineId: string; quantity: string }) =>
      salesApi.shipLine(orderId, lineId, quantity),
    onSuccess: () => {
      invalidate()
      setShipError(null)
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setShipError(message ?? 'Could not ship — check available stock.')
    },
  })

  const statusTone = {
    draft: 'slate',
    confirmed: 'blue',
    partially_shipped: 'amber',
    shipped: 'green',
    cancelled: 'red',
  } as const

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Sales" description="Customers and sales orders." />

      <Card
        title="Customers"
        icon={<Users className="h-4 w-4" />}
        actions={
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              createCustomer.mutate(customerForm)
            }}
          >
            <Input placeholder="Name" required value={customerForm.name} onChange={(e) => setCustomerForm({ ...customerForm, name: e.target.value })} className="w-40" />
            <Input placeholder="Code" required value={customerForm.code} onChange={(e) => setCustomerForm({ ...customerForm, code: e.target.value })} className="w-28" />
            <Button type="submit" disabled={createCustomer.isPending}>
              Add
            </Button>
          </form>
        }
      >
        {customers.length === 0 ? (
          <EmptyState message="No customers yet." />
        ) : (
          <Table headers={['Name', 'Code']}>
            {customers.map((c) => (
              <tr key={c.id}>
                <td className="px-3 py-2">{c.name}</td>
                <td className="px-3 py-2 text-slate-500">{c.code}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card title="Sales orders" icon={<ShoppingCart className="h-4 w-4" />}>
        {!selectedPlantId ? (
          <EmptyState message="Select a plant to manage sales orders." />
        ) : (
          <>
            {shipError && <Alert onDismiss={() => setShipError(null)}>{shipError}</Alert>}
            <form
              className="mb-4 flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                createOrder.mutate()
              }}
            >
              <Field label="Customer">
                <Select required value={orderForm.customer_id} onChange={(e) => setOrderForm({ ...orderForm, customer_id: e.target.value })} className="w-40">
                  <option value="">Select…</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
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
                Create SO
              </Button>
            </form>

            {orders.length === 0 ? (
              <EmptyState message="No sales orders yet." />
            ) : (
              <div className="flex flex-col gap-3">
                {orders.map((o) => (
                  <div key={o.id} className="rounded-md border border-slate-200 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{customers.find((c) => c.id === o.customer_id)?.name}</span>
                        <Badge tone={statusTone[o.status]}>{o.status.replace('_', ' ')}</Badge>
                      </div>
                      {o.status === 'draft' && (
                        <Button variant="secondary" onClick={() => confirmOrder.mutate(o.id)} disabled={confirmOrder.isPending}>
                          Confirm
                        </Button>
                      )}
                    </div>
                    <Table headers={['Item', 'Ordered', 'Shipped', 'Ship qty', '']}>
                      {o.lines.map((line) => (
                        <tr key={line.id}>
                          <td className="px-3 py-2 font-mono text-xs">{line.item_sku}</td>
                          <td className="px-3 py-2">{line.quantity_ordered}</td>
                          <td className="px-3 py-2">{line.quantity_shipped}</td>
                          <td className="px-3 py-2">
                            {(o.status === 'confirmed' || o.status === 'partially_shipped') && (
                              <Input
                                type="number"
                                step="any"
                                placeholder="Qty"
                                value={shipQuantities[line.id] ?? ''}
                                onChange={(e) => setShipQuantities({ ...shipQuantities, [line.id]: e.target.value })}
                                className="w-20"
                              />
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {(o.status === 'confirmed' || o.status === 'partially_shipped') && (
                              <Button
                                variant="secondary"
                                onClick={() =>
                                  shipLine.mutate({ orderId: o.id, lineId: line.id, quantity: shipQuantities[line.id] ?? '0' })
                                }
                                disabled={shipLine.isPending}
                              >
                                Ship
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </Table>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
