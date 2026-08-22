import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PackageCheck, PackageMinus, Warehouse as WarehouseIcon } from 'lucide-react'
import { inventoryApi, warehouseApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { Button, Card, EmptyState, Field, Input, PageHeader, Select, Table } from '../components/ui'

export function WarehousePage() {
  const queryClient = useQueryClient()
  const { selectedPlantId } = usePlant()

  const { data: items = [] } = useQuery({ queryKey: ['items'], queryFn: inventoryApi.listItems })
  const { data: warehouses = [] } = useQuery({
    queryKey: ['warehouses', selectedPlantId],
    queryFn: () => warehouseApi.listWarehouses(selectedPlantId ?? undefined),
  })
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('')
  const { data: zones = [] } = useQuery({
    queryKey: ['zones', selectedWarehouseId],
    queryFn: () => warehouseApi.listZones(selectedWarehouseId || undefined),
    enabled: !!selectedWarehouseId,
  })
  const { data: bins = [] } = useQuery({
    queryKey: ['bins', zones.map((z) => z.id).join(',')],
    queryFn: async () => (await Promise.all(zones.map((z) => warehouseApi.listBins(z.id)))).flat(),
    enabled: zones.length > 0,
  })
  const { data: binStock = [] } = useQuery({
    queryKey: ['bin-stock', selectedWarehouseId],
    queryFn: () => warehouseApi.listBinStock(selectedWarehouseId || undefined),
    enabled: !!selectedWarehouseId,
  })
  const [warehouseForm, setWarehouseForm] = useState({ name: '', code: '' })
  const [zoneForm, setZoneForm] = useState({ name: '', code: '', zone_type: 'storage' })
  const [binForm, setBinForm] = useState({ zone_id: '', code: '' })
  const [putawayForm, setPutawayForm] = useState({ item_id: '', destination_bin_id: '', quantity: '' })
  const [pickForm, setPickForm] = useState({ item_id: '', source_bin_id: '', quantity: '' })

  const invalidateBinStock = () => {
    queryClient.invalidateQueries({ queryKey: ['bin-stock'] })
    queryClient.invalidateQueries({ queryKey: ['balances'] })
  }

  const createWarehouse = useMutation({
    mutationFn: () => warehouseApi.createWarehouse({ plant_id: selectedPlantId!, ...warehouseForm }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      setWarehouseForm({ name: '', code: '' })
    },
  })
  const createZone = useMutation({
    mutationFn: () => warehouseApi.createZone({ warehouse_id: selectedWarehouseId, ...zoneForm }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] })
      setZoneForm({ name: '', code: '', zone_type: 'storage' })
    },
  })
  const createBin = useMutation({
    mutationFn: () => warehouseApi.createBin(binForm),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
      setBinForm({ zone_id: '', code: '' })
    },
  })
  const createAndCompletePutaway = useMutation({
    mutationFn: async () => {
      const task = await warehouseApi.createPutawayTask({ plant_id: selectedPlantId!, ...putawayForm })
      return warehouseApi.completePutawayTask(task.id)
    },
    onSuccess: () => {
      invalidateBinStock()
      setPutawayForm({ item_id: '', destination_bin_id: '', quantity: '' })
    },
  })
  const createAndCompletePick = useMutation({
    mutationFn: async () => {
      const task = await warehouseApi.createPickTask({ plant_id: selectedPlantId!, ...pickForm })
      return warehouseApi.completePickTask(task.id)
    },
    onSuccess: () => {
      invalidateBinStock()
      setPickForm({ item_id: '', source_bin_id: '', quantity: '' })
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Warehouse" description="Warehouses, zones, bins, and putaway/pick tasks." />

      {!selectedPlantId ? (
        <EmptyState message="Select a plant to manage warehouses." />
      ) : (
        <>
          <Card
            icon={<WarehouseIcon className="h-4 w-4" />}
            title="Warehouses"
            actions={
              <form
                className="flex items-end gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  createWarehouse.mutate()
                }}
              >
                <Input placeholder="Name" required value={warehouseForm.name} onChange={(e) => setWarehouseForm({ ...warehouseForm, name: e.target.value })} className="w-36" />
                <Input placeholder="Code" required value={warehouseForm.code} onChange={(e) => setWarehouseForm({ ...warehouseForm, code: e.target.value })} className="w-24" />
                <Button type="submit" disabled={createWarehouse.isPending}>
                  Add
                </Button>
              </form>
            }
          >
            {warehouses.length === 0 ? (
              <EmptyState message="No warehouses for this plant yet." />
            ) : (
              <Table headers={['Name', 'Code', '']}>
                {warehouses.map((w) => (
                  <tr key={w.id} className={w.id === selectedWarehouseId ? 'bg-indigo-50' : ''}>
                    <td className="px-3 py-2">{w.name}</td>
                    <td className="px-3 py-2 text-slate-500">{w.code}</td>
                    <td className="px-3 py-2">
                      <button className="text-xs font-medium text-indigo-600" onClick={() => setSelectedWarehouseId(w.id)}>
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>

          {selectedWarehouseId && (
            <>
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Card
                  title="Zones"
                  actions={
                    <form
                      className="flex items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault()
                        createZone.mutate()
                      }}
                    >
                      <Input placeholder="Name" required value={zoneForm.name} onChange={(e) => setZoneForm({ ...zoneForm, name: e.target.value })} className="w-24" />
                      <Input placeholder="Code" required value={zoneForm.code} onChange={(e) => setZoneForm({ ...zoneForm, code: e.target.value })} className="w-16" />
                      <Select value={zoneForm.zone_type} onChange={(e) => setZoneForm({ ...zoneForm, zone_type: e.target.value })} className="w-28">
                        <option value="receiving">Receiving</option>
                        <option value="storage">Storage</option>
                        <option value="picking">Picking</option>
                        <option value="shipping">Shipping</option>
                      </Select>
                      <Button type="submit" disabled={createZone.isPending}>
                        Add
                      </Button>
                    </form>
                  }
                >
                  {zones.length === 0 ? (
                    <EmptyState message="No zones yet." />
                  ) : (
                    <Table headers={['Name', 'Code', 'Type']}>
                      {zones.map((z) => (
                        <tr key={z.id}>
                          <td className="px-3 py-2">{z.name}</td>
                          <td className="px-3 py-2 text-slate-500">{z.code}</td>
                          <td className="px-3 py-2 text-slate-500">{z.zone_type}</td>
                        </tr>
                      ))}
                    </Table>
                  )}
                </Card>

                <Card
                  title="Bins"
                  actions={
                    <form
                      className="flex items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault()
                        createBin.mutate()
                      }}
                    >
                      <Select required value={binForm.zone_id} onChange={(e) => setBinForm({ ...binForm, zone_id: e.target.value })} className="w-28">
                        <option value="">Zone…</option>
                        {zones.map((z) => (
                          <option key={z.id} value={z.id}>
                            {z.code}
                          </option>
                        ))}
                      </Select>
                      <Input placeholder="Code" required value={binForm.code} onChange={(e) => setBinForm({ ...binForm, code: e.target.value })} className="w-20" />
                      <Button type="submit" disabled={createBin.isPending}>
                        Add
                      </Button>
                    </form>
                  }
                >
                  {bins.length === 0 ? (
                    <EmptyState message="No bins yet." />
                  ) : (
                    <Table headers={['Code', 'Zone']}>
                      {bins.map((b) => (
                        <tr key={b.id}>
                          <td className="px-3 py-2 font-mono text-xs">{b.code}</td>
                          <td className="px-3 py-2 text-slate-500">{zones.find((z) => z.id === b.zone_id)?.code}</td>
                        </tr>
                      ))}
                    </Table>
                  )}
                </Card>
              </div>

              <Card title="Bin stock">
                {binStock.length === 0 ? (
                  <EmptyState message="No stock in bins yet." />
                ) : (
                  <Table headers={['Bin', 'SKU', 'Quantity']}>
                    {binStock.map((s) => (
                      <tr key={`${s.bin_id}-${s.item_id}`}>
                        <td className="px-3 py-2 font-mono text-xs">{s.bin_code}</td>
                        <td className="px-3 py-2 font-mono text-xs">{s.item_sku}</td>
                        <td className="px-3 py-2">{s.quantity}</td>
                      </tr>
                    ))}
                  </Table>
                )}
              </Card>

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Card title="Putaway (receive into bin)" icon={<PackageCheck className="h-4 w-4" />}>
                  <form
                    className="flex flex-wrap items-end gap-2"
                    onSubmit={(e) => {
                      e.preventDefault()
                      createAndCompletePutaway.mutate()
                    }}
                  >
                    <Field label="Item">
                      <Select required value={putawayForm.item_id} onChange={(e) => setPutawayForm({ ...putawayForm, item_id: e.target.value })} className="w-36">
                        <option value="">Item…</option>
                        {items.map((i) => (
                          <option key={i.id} value={i.id}>
                            {i.sku}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Bin">
                      <Select required value={putawayForm.destination_bin_id} onChange={(e) => setPutawayForm({ ...putawayForm, destination_bin_id: e.target.value })} className="w-28">
                        <option value="">Bin…</option>
                        {bins.map((b) => (
                          <option key={b.id} value={b.id}>
                            {b.code}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Qty">
                      <Input required type="number" step="any" value={putawayForm.quantity} onChange={(e) => setPutawayForm({ ...putawayForm, quantity: e.target.value })} className="w-24" />
                    </Field>
                    <Button type="submit" disabled={createAndCompletePutaway.isPending}>
                      Putaway
                    </Button>
                  </form>
                </Card>

                <Card title="Pick (ship out of bin)" icon={<PackageMinus className="h-4 w-4" />}>
                  <form
                    className="flex flex-wrap items-end gap-2"
                    onSubmit={(e) => {
                      e.preventDefault()
                      createAndCompletePick.mutate()
                    }}
                  >
                    <Field label="Item">
                      <Select required value={pickForm.item_id} onChange={(e) => setPickForm({ ...pickForm, item_id: e.target.value })} className="w-36">
                        <option value="">Item…</option>
                        {items.map((i) => (
                          <option key={i.id} value={i.id}>
                            {i.sku}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Bin">
                      <Select required value={pickForm.source_bin_id} onChange={(e) => setPickForm({ ...pickForm, source_bin_id: e.target.value })} className="w-28">
                        <option value="">Bin…</option>
                        {bins.map((b) => (
                          <option key={b.id} value={b.id}>
                            {b.code}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Field label="Qty">
                      <Input required type="number" step="any" value={pickForm.quantity} onChange={(e) => setPickForm({ ...pickForm, quantity: e.target.value })} className="w-24" />
                    </Field>
                    <Button type="submit" disabled={createAndCompletePick.isPending}>
                      Pick
                    </Button>
                  </form>
                  {createAndCompletePick.isError && (
                    <p className="mt-2 text-sm text-red-600">Pick failed — check bin stock is sufficient.</p>
                  )}
                </Card>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
