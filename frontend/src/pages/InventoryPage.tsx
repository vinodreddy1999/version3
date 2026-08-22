import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeftRight, Boxes, Package } from 'lucide-react'
import { inventoryApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { Alert, Badge, Button, Card, EmptyState, Field, Input, PageHeader, Select, Table } from '../components/ui'

export function InventoryPage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: balances = [] } = useQuery({
    queryKey: ['balances', selectedPlantId],
    queryFn: () => inventoryApi.listBalances(selectedPlantId ?? undefined),
  })
  const { data: movements = [] } = useQuery({
    queryKey: ['movements', selectedPlantId],
    queryFn: () => inventoryApi.listMovements(selectedPlantId ?? undefined),
  })

  const [itemForm, setItemForm] = useState({ sku: '', name: '', item_type: 'raw_material', uom: 'EA' })
  const [movementForm, setMovementForm] = useState({ item_id: '', movement_type: 'receipt', quantity: '' })
  const [formError, setFormError] = useState<string | null>(null)

  const createItem = useMutation({
    mutationFn: inventoryApi.createItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] })
      setItemForm({ sku: '', name: '', item_type: 'raw_material', uom: 'EA' })
    },
  })

  const createMovement = useMutation({
    mutationFn: inventoryApi.createMovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['balances'] })
      queryClient.invalidateQueries({ queryKey: ['movements'] })
      setMovementForm({ item_id: '', movement_type: 'receipt', quantity: '' })
      setFormError(null)
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setFormError(message ?? 'Could not record movement.')
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Inventory" description="Items, stock balances, and the movement ledger." />

      <Card title="Items" icon={<Package className="h-4 w-4" />}>
        <form
          className="mb-4 flex flex-wrap items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            createItem.mutate(itemForm)
          }}
        >
          <Field label="SKU">
            <Input required value={itemForm.sku} onChange={(e) => setItemForm({ ...itemForm, sku: e.target.value })} className="w-32" />
          </Field>
          <Field label="Name">
            <Input required value={itemForm.name} onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })} className="w-48" />
          </Field>
          <Field label="Type">
            <Select value={itemForm.item_type} onChange={(e) => setItemForm({ ...itemForm, item_type: e.target.value })} className="w-40">
              <option value="raw_material">Raw material</option>
              <option value="work_in_progress">Work in progress</option>
              <option value="finished_good">Finished good</option>
              <option value="consumable">Consumable</option>
            </Select>
          </Field>
          <Field label="UoM">
            <Input value={itemForm.uom} onChange={(e) => setItemForm({ ...itemForm, uom: e.target.value })} className="w-20" />
          </Field>
          <Button type="submit" disabled={createItem.isPending}>
            Add item
          </Button>
        </form>

        {items.length === 0 ? (
          <EmptyState message="No items yet." />
        ) : (
          <Table headers={['SKU', 'Name', 'Type', 'UoM', 'Reorder point']}>
            {items.map((item) => (
              <tr key={item.id}>
                <td className="px-3 py-2 font-mono text-xs">{item.sku}</td>
                <td className="px-3 py-2">{item.name}</td>
                <td className="px-3 py-2 text-slate-500">{item.item_type.replace(/_/g, ' ')}</td>
                <td className="px-3 py-2 text-slate-500">{item.uom}</td>
                <td className="px-3 py-2 text-slate-500">{item.reorder_point}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card title="Stock balances" icon={<Boxes className="h-4 w-4" />}>
        {balances.length === 0 ? (
          <EmptyState message="No stock recorded yet for this plant." />
        ) : (
          <Table headers={['SKU', 'Name', 'On hand', 'Reserved', 'Available']}>
            {balances.map((b) => (
              <tr key={b.id}>
                <td className="px-3 py-2 font-mono text-xs">{b.item_sku}</td>
                <td className="px-3 py-2">{b.item_name}</td>
                <td className="px-3 py-2">{b.quantity_on_hand}</td>
                <td className="px-3 py-2 text-slate-500">{b.quantity_reserved}</td>
                <td className="px-3 py-2 font-medium">{b.quantity_available}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card title="Post a stock movement" icon={<ArrowLeftRight className="h-4 w-4" />}>
        {!selectedPlantId ? (
          <EmptyState message="Select a plant to post movements." />
        ) : (
          <>
            {formError && <Alert onDismiss={() => setFormError(null)}>{formError}</Alert>}
            <form
              className="flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                createMovement.mutate({ plant_id: selectedPlantId, ...movementForm })
              }}
            >
              <Field label="Item">
                <Select
                  required
                  value={movementForm.item_id}
                  onChange={(e) => setMovementForm({ ...movementForm, item_id: e.target.value })}
                  className="w-48"
                >
                  <option value="">Select item…</option>
                  {items.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.sku} — {item.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Type">
                <Select
                  value={movementForm.movement_type}
                  onChange={(e) => setMovementForm({ ...movementForm, movement_type: e.target.value })}
                  className="w-36"
                >
                  <option value="receipt">Receipt</option>
                  <option value="issue">Issue</option>
                  <option value="adjustment">Adjustment</option>
                </Select>
              </Field>
              <Field label="Quantity">
                <Input
                  required
                  type="number"
                  step="any"
                  value={movementForm.quantity}
                  onChange={(e) => setMovementForm({ ...movementForm, quantity: e.target.value })}
                  className="w-28"
                />
              </Field>
              <Button type="submit" disabled={createMovement.isPending}>
                Post
              </Button>
            </form>
          </>
        )}
      </Card>

      <Card title="Recent movements">
        {movements.length === 0 ? (
          <EmptyState message="No movements recorded yet." />
        ) : (
          <Table headers={['Item', 'Type', 'Quantity', 'Reference']}>
            {movements.map((m) => (
              <tr key={m.id}>
                <td className="px-3 py-2">{items.find((i) => i.id === m.item_id)?.sku ?? m.item_id}</td>
                <td className="px-3 py-2">
                  <Badge tone={m.movement_type === 'issue' ? 'red' : 'green'}>{m.movement_type}</Badge>
                </td>
                <td className="px-3 py-2">{m.quantity}</td>
                <td className="px-3 py-2 text-slate-500">{m.reference ?? '—'}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  )
}
