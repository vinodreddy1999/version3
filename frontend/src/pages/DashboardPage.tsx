import { useQuery } from '@tanstack/react-query'
import {
  Boxes,
  ClipboardCheck,
  Factory,
  ShoppingCart,
  Truck,
  Warehouse as WarehouseIcon,
  Wrench,
} from 'lucide-react'
import { reportsApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { Card, PageHeader, StatCard } from '../components/ui'

export function DashboardPage() {
  const { selectedPlantId } = usePlant()
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', selectedPlantId],
    queryFn: () => reportsApi.dashboard(selectedPlantId ?? undefined),
  })

  if (isLoading) return <p className="text-sm text-slate-500">Loading dashboard…</p>
  if (error || !data) return <p className="text-sm text-red-600">Could not load dashboard data.</p>

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Dashboard" description="Live numbers pulled straight from every module below." />

      <Card title="Inventory" icon={<Boxes className="h-4 w-4" />}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Active items" value={data.inventory.active_item_count} />
          <StatCard label="Total on hand" value={data.inventory.total_quantity_on_hand} />
          <StatCard
            label="Low stock items"
            value={data.inventory.low_stock_item_count}
            tone={data.inventory.low_stock_item_count > 0 ? 'warn' : 'default'}
          />
        </div>
      </Card>

      <Card title="Warehouse" icon={<WarehouseIcon className="h-4 w-4" />}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <StatCard label="Pending putaway tasks" value={data.warehouse.pending_putaway_tasks} />
          <StatCard label="Pending pick tasks" value={data.warehouse.pending_pick_tasks} />
        </div>
      </Card>

      <Card title="Production" icon={<Factory className="h-4 w-4" />}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <StatCard label="Open orders" value={data.production.open_orders} />
          <StatCard label="In progress" value={data.production.in_progress_orders} tone="warn" />
          <StatCard label="Completed" value={data.production.completed_orders} tone="good" />
          <StatCard label="Total qty completed" value={data.production.total_quantity_completed} />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Procurement" icon={<ShoppingCart className="h-4 w-4" />}>
          <div className="grid grid-cols-2 gap-4">
            <StatCard label="Open purchase orders" value={data.procurement.open_purchase_orders} />
            <StatCard label="Outstanding qty ordered" value={data.procurement.outstanding_quantity_ordered} />
          </div>
        </Card>
        <Card title="Sales" icon={<Truck className="h-4 w-4" />}>
          <div className="grid grid-cols-2 gap-4">
            <StatCard label="Open sales orders" value={data.sales.open_sales_orders} />
            <StatCard label="Outstanding qty to ship" value={data.sales.outstanding_quantity_to_ship} />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Maintenance" icon={<Wrench className="h-4 w-4" />}>
          <div className="grid grid-cols-2 gap-4">
            <StatCard label="Open work orders" value={data.maintenance.open_work_orders} />
            <StatCard
              label="Assets down/in maintenance"
              value={data.maintenance.assets_down_or_in_maintenance}
              tone={data.maintenance.assets_down_or_in_maintenance > 0 ? 'bad' : 'default'}
            />
          </div>
        </Card>
        <Card title="Quality" icon={<ClipboardCheck className="h-4 w-4" />}>
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Inspections" value={data.quality.total_inspections} />
            <StatCard
              label="Failed"
              value={data.quality.failed_inspections}
              tone={data.quality.failed_inspections > 0 ? 'bad' : 'default'}
            />
            <StatCard label="Open defects" value={data.quality.open_defects} />
          </div>
        </Card>
      </div>
    </div>
  )
}
