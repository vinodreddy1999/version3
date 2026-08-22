import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '../api/endpoints'
import { usePlant } from '../contexts/PlantContext'
import { Card } from '../components/ui'

function Stat({ label, value, tone = 'text-slate-900' }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p>
    </div>
  )
}

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
      <h1 className="text-xl font-bold text-slate-800">Dashboard</h1>

      <Card title="Inventory">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Stat label="Active items" value={data.inventory.active_item_count} />
          <Stat label="Total on hand" value={data.inventory.total_quantity_on_hand} />
          <Stat
            label="Low stock items"
            value={data.inventory.low_stock_item_count}
            tone={data.inventory.low_stock_item_count > 0 ? 'text-amber-600' : 'text-slate-900'}
          />
        </div>
      </Card>

      <Card title="Warehouse">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Stat label="Pending putaway tasks" value={data.warehouse.pending_putaway_tasks} />
          <Stat label="Pending pick tasks" value={data.warehouse.pending_pick_tasks} />
        </div>
      </Card>

      <Card title="Production">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <Stat label="Open orders" value={data.production.open_orders} />
          <Stat label="In progress" value={data.production.in_progress_orders} />
          <Stat label="Completed" value={data.production.completed_orders} />
          <Stat label="Total qty completed" value={data.production.total_quantity_completed} />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Procurement">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Open purchase orders" value={data.procurement.open_purchase_orders} />
            <Stat label="Outstanding qty ordered" value={data.procurement.outstanding_quantity_ordered} />
          </div>
        </Card>
        <Card title="Sales">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Open sales orders" value={data.sales.open_sales_orders} />
            <Stat label="Outstanding qty to ship" value={data.sales.outstanding_quantity_to_ship} />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Maintenance">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Open work orders" value={data.maintenance.open_work_orders} />
            <Stat
              label="Assets down/in maintenance"
              value={data.maintenance.assets_down_or_in_maintenance}
              tone={data.maintenance.assets_down_or_in_maintenance > 0 ? 'text-red-600' : 'text-slate-900'}
            />
          </div>
        </Card>
        <Card title="Quality">
          <div className="grid grid-cols-3 gap-4">
            <Stat label="Inspections" value={data.quality.total_inspections} />
            <Stat
              label="Failed"
              value={data.quality.failed_inspections}
              tone={data.quality.failed_inspections > 0 ? 'text-red-600' : 'text-slate-900'}
            />
            <Stat label="Open defects" value={data.quality.open_defects} />
          </div>
        </Card>
      </div>
    </div>
  )
}
