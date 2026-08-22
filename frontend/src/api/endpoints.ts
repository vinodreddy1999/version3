import { apiClient, toPaginated } from '../lib/apiClient'
import type {
  AdminUser,
  Asset,
  AuditLogEntry,
  BillOfMaterial,
  Bin,
  BinStock,
  Company,
  CurrentUser,
  Customer,
  Dashboard,
  Inspection,
  Item,
  MaintenanceWorkOrder,
  Paginated,
  Permission,
  PickTask,
  Plant,
  ProductionOrder,
  PurchaseOrder,
  PutawayTask,
  Role,
  SalesOrder,
  StockBalance,
  StockMovement,
  Supplier,
  TokenResponse,
  Warehouse,
  WorkCenter,
  Zone,
} from './types'

export interface PageParams {
  limit?: number
  offset?: number
}

export const authApi = {
  registerTenant: (payload: {
    tenant_name: string
    tenant_slug: string
    admin_email: string
    admin_password: string
    admin_full_name: string
  }) => apiClient.post<TokenResponse>('/api/auth/register-tenant', payload).then((r) => r.data),

  login: (payload: { email: string; password: string; tenant_slug: string }) =>
    apiClient.post<TokenResponse>('/api/auth/login', payload).then((r) => r.data),

  me: () => apiClient.get<CurrentUser>('/api/auth/me').then((r) => r.data),
}

export const orgApi = {
  listCompanies: () => apiClient.get<Company[]>('/api/org/companies').then((r) => r.data),
  createCompany: (payload: { name: string; code: string }) =>
    apiClient.post<Company>('/api/org/companies', payload).then((r) => r.data),

  listPlants: (companyId?: string) =>
    apiClient.get<Plant[]>('/api/org/plants', { params: { company_id: companyId } }).then((r) => r.data),
  createPlant: (payload: { company_id: string; name: string; code: string; address?: string }) =>
    apiClient.post<Plant>('/api/org/plants', payload).then((r) => r.data),
}

export const inventoryApi = {
  listItems: () => apiClient.get<Item[]>('/api/inventory/items').then((r) => r.data),
  createItem: (payload: {
    sku: string
    name: string
    item_type: string
    uom?: string
    reorder_point?: string
    description?: string
  }) => apiClient.post<Item>('/api/inventory/items', payload).then((r) => r.data),

  listBalances: (plantId?: string) =>
    apiClient.get<StockBalance[]>('/api/inventory/balances', { params: { plant_id: plantId } }).then((r) => r.data),

  listMovements: (plantId?: string, page?: PageParams): Promise<Paginated<StockMovement>> =>
    apiClient
      .get<StockMovement[]>('/api/inventory/movements', { params: { plant_id: plantId, ...page } })
      .then(toPaginated),
  createMovement: (payload: {
    plant_id: string
    item_id: string
    movement_type: string
    quantity: string
    reference?: string
    notes?: string
  }) => apiClient.post<StockMovement>('/api/inventory/movements', payload).then((r) => r.data),
}

export const warehouseApi = {
  listWarehouses: (plantId?: string) =>
    apiClient.get<Warehouse[]>('/api/warehouse/warehouses', { params: { plant_id: plantId } }).then((r) => r.data),
  createWarehouse: (payload: { plant_id: string; name: string; code: string }) =>
    apiClient.post<Warehouse>('/api/warehouse/warehouses', payload).then((r) => r.data),

  listZones: (warehouseId?: string) =>
    apiClient.get<Zone[]>('/api/warehouse/zones', { params: { warehouse_id: warehouseId } }).then((r) => r.data),
  createZone: (payload: { warehouse_id: string; name: string; code: string; zone_type: string }) =>
    apiClient.post<Zone>('/api/warehouse/zones', payload).then((r) => r.data),

  listBins: (zoneId?: string) =>
    apiClient.get<Bin[]>('/api/warehouse/bins', { params: { zone_id: zoneId } }).then((r) => r.data),
  createBin: (payload: { zone_id: string; code: string }) =>
    apiClient.post<Bin>('/api/warehouse/bins', payload).then((r) => r.data),

  listBinStock: (warehouseId?: string) =>
    apiClient.get<BinStock[]>('/api/warehouse/bin-stock', { params: { warehouse_id: warehouseId } }).then((r) => r.data),

  createPutawayTask: (payload: {
    plant_id: string
    item_id: string
    destination_bin_id: string
    quantity: string
    reference?: string
  }) => apiClient.post<PutawayTask>('/api/warehouse/putaway-tasks', payload).then((r) => r.data),
  completePutawayTask: (id: string) =>
    apiClient.post<PutawayTask>(`/api/warehouse/putaway-tasks/${id}/complete`).then((r) => r.data),

  createPickTask: (payload: { plant_id: string; item_id: string; source_bin_id: string; quantity: string; reference?: string }) =>
    apiClient.post<PickTask>('/api/warehouse/pick-tasks', payload).then((r) => r.data),
  completePickTask: (id: string) =>
    apiClient.post<PickTask>(`/api/warehouse/pick-tasks/${id}/complete`).then((r) => r.data),
}

export const productionApi = {
  listWorkCenters: (plantId?: string) =>
    apiClient.get<WorkCenter[]>('/api/production/work-centers', { params: { plant_id: plantId } }).then((r) => r.data),
  createWorkCenter: (payload: { plant_id: string; name: string; code: string; capacity_per_hour?: string }) =>
    apiClient.post<WorkCenter>('/api/production/work-centers', payload).then((r) => r.data),

  listBoms: () => apiClient.get<BillOfMaterial[]>('/api/production/boms').then((r) => r.data),
  createBom: (payload: {
    output_item_id: string
    name: string
    version?: string
    components: { component_item_id: string; quantity_per_unit: string }[]
  }) => apiClient.post<BillOfMaterial>('/api/production/boms', payload).then((r) => r.data),

  listOrders: (plantId?: string, page?: PageParams): Promise<Paginated<ProductionOrder>> =>
    apiClient
      .get<ProductionOrder[]>('/api/production/orders', { params: { plant_id: plantId, ...page } })
      .then(toPaginated),
  createOrder: (payload: { plant_id: string; bom_id: string; quantity_planned: string; reference?: string }) =>
    apiClient.post<ProductionOrder>('/api/production/orders', payload).then((r) => r.data),
  completeOrder: (id: string, quantity: string) =>
    apiClient.post<ProductionOrder>(`/api/production/orders/${id}/complete`, { quantity }).then((r) => r.data),
}

export const procurementApi = {
  listSuppliers: () => apiClient.get<Supplier[]>('/api/procurement/suppliers').then((r) => r.data),
  createSupplier: (payload: { name: string; code: string; contact_email?: string; contact_phone?: string }) =>
    apiClient.post<Supplier>('/api/procurement/suppliers', payload).then((r) => r.data),

  listOrders: (plantId?: string, page?: PageParams): Promise<Paginated<PurchaseOrder>> =>
    apiClient
      .get<PurchaseOrder[]>('/api/procurement/orders', { params: { plant_id: plantId, ...page } })
      .then(toPaginated),
  createOrder: (payload: {
    plant_id: string
    supplier_id: string
    reference?: string
    lines: { item_id: string; quantity_ordered: string; unit_price?: string }[]
  }) => apiClient.post<PurchaseOrder>('/api/procurement/orders', payload).then((r) => r.data),
  submitOrder: (id: string) => apiClient.post<PurchaseOrder>(`/api/procurement/orders/${id}/submit`).then((r) => r.data),
  receiveLine: (id: string, lineId: string, quantity: string) =>
    apiClient
      .post<PurchaseOrder>(`/api/procurement/orders/${id}/receive`, { line_id: lineId, quantity })
      .then((r) => r.data),
}

export const salesApi = {
  listCustomers: () => apiClient.get<Customer[]>('/api/sales/customers').then((r) => r.data),
  createCustomer: (payload: { name: string; code: string; contact_email?: string; contact_phone?: string }) =>
    apiClient.post<Customer>('/api/sales/customers', payload).then((r) => r.data),

  listOrders: (plantId?: string, page?: PageParams): Promise<Paginated<SalesOrder>> =>
    apiClient.get<SalesOrder[]>('/api/sales/orders', { params: { plant_id: plantId, ...page } }).then(toPaginated),
  createOrder: (payload: {
    plant_id: string
    customer_id: string
    reference?: string
    lines: { item_id: string; quantity_ordered: string; unit_price?: string }[]
  }) => apiClient.post<SalesOrder>('/api/sales/orders', payload).then((r) => r.data),
  confirmOrder: (id: string) => apiClient.post<SalesOrder>(`/api/sales/orders/${id}/confirm`).then((r) => r.data),
  shipLine: (id: string, lineId: string, quantity: string) =>
    apiClient.post<SalesOrder>(`/api/sales/orders/${id}/ship`, { line_id: lineId, quantity }).then((r) => r.data),
}

export const maintenanceApi = {
  listAssets: (plantId?: string) =>
    apiClient.get<Asset[]>('/api/maintenance/assets', { params: { plant_id: plantId } }).then((r) => r.data),
  createAsset: (payload: { plant_id: string; name: string; code: string }) =>
    apiClient.post<Asset>('/api/maintenance/assets', payload).then((r) => r.data),

  listWorkOrders: (plantId?: string, page?: PageParams): Promise<Paginated<MaintenanceWorkOrder>> =>
    apiClient
      .get<MaintenanceWorkOrder[]>('/api/maintenance/work-orders', { params: { plant_id: plantId, ...page } })
      .then(toPaginated),
  createWorkOrder: (payload: { plant_id: string; asset_id: string; work_order_type: string; priority?: string; description?: string }) =>
    apiClient.post<MaintenanceWorkOrder>('/api/maintenance/work-orders', payload).then((r) => r.data),
  startWorkOrder: (id: string) =>
    apiClient.post<MaintenanceWorkOrder>(`/api/maintenance/work-orders/${id}/start`).then((r) => r.data),
  completeWorkOrder: (id: string) =>
    apiClient.post<MaintenanceWorkOrder>(`/api/maintenance/work-orders/${id}/complete`).then((r) => r.data),
  cancelWorkOrder: (id: string) =>
    apiClient.post<MaintenanceWorkOrder>(`/api/maintenance/work-orders/${id}/cancel`).then((r) => r.data),
}

export const qualityApi = {
  listInspections: (plantId?: string, page?: PageParams): Promise<Paginated<Inspection>> =>
    apiClient
      .get<Inspection[]>('/api/quality/inspections', { params: { plant_id: plantId, ...page } })
      .then(toPaginated),
  createInspection: (payload: {
    plant_id: string
    item_id: string
    inspected_quantity: string
    reference?: string
    notes?: string
    defects?: { defect_type: string; severity: string; quantity: string; description?: string }[]
  }) => apiClient.post<Inspection>('/api/quality/inspections', payload).then((r) => r.data),
  resolveDefect: (defectId: string) =>
    apiClient.post<Inspection>(`/api/quality/defects/${defectId}/resolve`).then((r) => r.data),
}

export const adminApi = {
  listPermissions: () => apiClient.get<Permission[]>('/api/admin/permissions').then((r) => r.data),

  listRoles: () => apiClient.get<Role[]>('/api/admin/roles').then((r) => r.data),
  createRole: (payload: { name: string; permission_codes: string[] }) =>
    apiClient.post<Role>('/api/admin/roles', payload).then((r) => r.data),
  updateRole: (id: string, payload: { name?: string; permission_codes?: string[] }) =>
    apiClient.patch<Role>(`/api/admin/roles/${id}`, payload).then((r) => r.data),
  deleteRole: (id: string) => apiClient.delete(`/api/admin/roles/${id}`),

  listUsers: (page?: PageParams): Promise<Paginated<AdminUser>> =>
    apiClient.get<AdminUser[]>('/api/admin/users', { params: page }).then(toPaginated),
  createUser: (payload: { email: string; full_name: string; password: string; role_ids: string[]; is_superuser?: boolean }) =>
    apiClient.post<AdminUser>('/api/admin/users', payload).then((r) => r.data),
  updateUser: (
    id: string,
    payload: { full_name?: string; is_active?: boolean; is_superuser?: boolean; role_ids?: string[] },
  ) => apiClient.patch<AdminUser>(`/api/admin/users/${id}`, payload).then((r) => r.data),

  listAuditLog: (page?: PageParams): Promise<Paginated<AuditLogEntry>> =>
    apiClient.get<AuditLogEntry[]>('/api/admin/audit-log', { params: page }).then(toPaginated),
}

export const reportsApi = {
  dashboard: (plantId?: string) =>
    apiClient.get<Dashboard>('/api/reports/dashboard', { params: { plant_id: plantId } }).then((r) => r.data),
}
