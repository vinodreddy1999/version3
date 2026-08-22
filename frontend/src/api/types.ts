export interface Paginated<T> {
  items: T[]
  total: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface CurrentUser {
  id: string
  email: string
  full_name: string
  tenant_id: string
  is_superuser: boolean
  roles: string[]
  permissions: string[]
}

export interface Permission {
  code: string
  description: string | null
}

export interface Role {
  id: string
  name: string
  is_system: boolean
  permission_codes: string[]
}

export interface AdminUser {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  role_ids: string[]
  role_names: string[]
}

export interface Company {
  id: string
  name: string
  code: string
  is_active: boolean
}

export interface Plant {
  id: string
  company_id: string
  name: string
  code: string
  address: string | null
  is_active: boolean
}

export type ItemType = 'raw_material' | 'work_in_progress' | 'finished_good' | 'consumable'

export interface Item {
  id: string
  sku: string
  name: string
  description: string | null
  item_type: ItemType
  uom: string
  reorder_point: string
  is_active: boolean
}

export interface StockBalance {
  id: string
  plant_id: string
  item_id: string
  item_sku: string
  item_name: string
  quantity_on_hand: string
  quantity_reserved: string
  quantity_available: string
}

export type MovementType = 'receipt' | 'issue' | 'adjustment' | 'transfer_in' | 'transfer_out'

export interface StockMovement {
  id: string
  plant_id: string
  item_id: string
  movement_type: MovementType
  quantity: string
  reference: string | null
  notes: string | null
  created_by_user_id: string
}

export interface Warehouse {
  id: string
  plant_id: string
  name: string
  code: string
}

export type ZoneType = 'receiving' | 'storage' | 'picking' | 'shipping'

export interface Zone {
  id: string
  warehouse_id: string
  name: string
  code: string
  zone_type: ZoneType
}

export interface Bin {
  id: string
  zone_id: string
  code: string
}

export interface BinStock {
  bin_id: string
  bin_code: string
  item_id: string
  item_sku: string
  quantity: string
}

export type TaskStatus = 'pending' | 'completed' | 'cancelled'

export interface PutawayTask {
  id: string
  plant_id: string
  item_id: string
  destination_bin_id: string
  quantity: string
  reference: string | null
  status: TaskStatus
}

export interface PickTask {
  id: string
  plant_id: string
  item_id: string
  source_bin_id: string
  quantity: string
  reference: string | null
  status: TaskStatus
}

export interface WorkCenter {
  id: string
  plant_id: string
  name: string
  code: string
  capacity_per_hour: string | null
}

export interface BOMComponent {
  component_item_id: string
  component_sku: string
  quantity_per_unit: string
}

export interface BillOfMaterial {
  id: string
  output_item_id: string
  name: string
  version: string
  is_active: boolean
  components: BOMComponent[]
}

export type ProductionOrderStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled'

export interface ProductionOrder {
  id: string
  plant_id: string
  bom_id: string
  work_center_id: string | null
  quantity_planned: string
  quantity_completed: string
  status: ProductionOrderStatus
  reference: string | null
}

export interface Supplier {
  id: string
  name: string
  code: string
  contact_email: string | null
  contact_phone: string | null
  is_active: boolean
}

export type PurchaseOrderStatus = 'draft' | 'submitted' | 'partially_received' | 'received' | 'cancelled'

export interface PurchaseOrderLine {
  id: string
  item_id: string
  item_sku: string
  quantity_ordered: string
  quantity_received: string
  unit_price: string
}

export interface PurchaseOrder {
  id: string
  plant_id: string
  supplier_id: string
  reference: string | null
  status: PurchaseOrderStatus
  lines: PurchaseOrderLine[]
}

export interface Customer {
  id: string
  name: string
  code: string
  contact_email: string | null
  contact_phone: string | null
  is_active: boolean
}

export type SalesOrderStatus = 'draft' | 'confirmed' | 'partially_shipped' | 'shipped' | 'cancelled'

export interface SalesOrderLine {
  id: string
  item_id: string
  item_sku: string
  quantity_ordered: string
  quantity_shipped: string
  unit_price: string
}

export interface SalesOrder {
  id: string
  plant_id: string
  customer_id: string
  reference: string | null
  status: SalesOrderStatus
  lines: SalesOrderLine[]
}

export type AssetStatus = 'operational' | 'down' | 'maintenance'

export interface Asset {
  id: string
  plant_id: string
  name: string
  code: string
  status: AssetStatus
  is_active: boolean
}

export type WorkOrderType = 'preventive' | 'corrective' | 'inspection'
export type WorkOrderPriority = 'low' | 'medium' | 'high' | 'critical'
export type WorkOrderStatus = 'open' | 'in_progress' | 'completed' | 'cancelled'

export interface MaintenanceWorkOrder {
  id: string
  plant_id: string
  asset_id: string
  work_order_type: WorkOrderType
  priority: WorkOrderPriority
  status: WorkOrderStatus
  description: string | null
}

export type DefectSeverity = 'minor' | 'major' | 'critical'
export type DefectStatus = 'open' | 'resolved'

export interface Defect {
  id: string
  defect_type: string
  severity: DefectSeverity
  quantity: string
  description: string | null
  status: DefectStatus
}

export type InspectionResult = 'pass' | 'fail'

export interface Inspection {
  id: string
  plant_id: string
  item_id: string
  reference: string | null
  inspected_quantity: string
  result: InspectionResult
  notes: string | null
  defects: Defect[]
}

export interface Dashboard {
  inventory: { active_item_count: number; total_quantity_on_hand: string; low_stock_item_count: number }
  warehouse: { pending_putaway_tasks: number; pending_pick_tasks: number }
  production: {
    open_orders: number
    in_progress_orders: number
    completed_orders: number
    total_quantity_completed: string
  }
  procurement: { open_purchase_orders: number; outstanding_quantity_ordered: string }
  sales: { open_sales_orders: number; outstanding_quantity_to_ship: string }
  maintenance: { open_work_orders: number; assets_down_or_in_maintenance: number }
  quality: { total_inspections: number; failed_inspections: number; open_defects: number }
}
