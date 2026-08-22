from decimal import Decimal

from pydantic import BaseModel


class InventorySummary(BaseModel):
    active_item_count: int
    total_quantity_on_hand: Decimal
    low_stock_item_count: int


class WarehouseSummary(BaseModel):
    pending_putaway_tasks: int
    pending_pick_tasks: int


class ProductionSummary(BaseModel):
    open_orders: int
    in_progress_orders: int
    completed_orders: int
    total_quantity_completed: Decimal


class ProcurementSummary(BaseModel):
    open_purchase_orders: int
    outstanding_quantity_ordered: Decimal


class SalesSummary(BaseModel):
    open_sales_orders: int
    outstanding_quantity_to_ship: Decimal


class MaintenanceSummary(BaseModel):
    open_work_orders: int
    assets_down_or_in_maintenance: int


class QualitySummary(BaseModel):
    total_inspections: int
    failed_inspections: int
    open_defects: int


class DashboardOut(BaseModel):
    inventory: InventorySummary
    warehouse: WarehouseSummary
    production: ProductionSummary
    procurement: ProcurementSummary
    sales: SalesSummary
    maintenance: MaintenanceSummary
    quality: QualitySummary
