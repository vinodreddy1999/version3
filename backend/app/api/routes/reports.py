from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.inventory import Item, StockBalance
from app.models.maintenance import Asset, AssetStatus, MaintenanceWorkOrder, WorkOrderStatus
from app.models.procurement import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from app.models.production import ProductionOrder, ProductionOrderStatus
from app.models.quality import Defect, DefectStatus, Inspection, InspectionResult
from app.models.sales import SalesOrder, SalesOrderLine, SalesOrderStatus
from app.models.user import User
from app.models.warehouse import PickTask, PutawayTask, TaskStatus
from app.schemas.reports import (
    DashboardOut,
    InventorySummary,
    MaintenanceSummary,
    ProcurementSummary,
    ProductionSummary,
    QualitySummary,
    SalesSummary,
    WarehouseSummary,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _inventory_summary(db: Session, user: User, plant_id: str | None) -> InventorySummary:
    items = db.query(Item).filter(Item.tenant_id == user.tenant_id, Item.is_active.is_(True)).all()

    balance_query = db.query(StockBalance).filter(StockBalance.tenant_id == user.tenant_id)
    if plant_id:
        balance_query = balance_query.filter(StockBalance.plant_id == plant_id)

    on_hand_by_item: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for balance in balance_query.all():
        on_hand_by_item[balance.item_id] += balance.quantity_on_hand

    total_on_hand = sum(on_hand_by_item.values(), Decimal("0"))
    low_stock_count = sum(1 for item in items if on_hand_by_item[item.id] < item.reorder_point)

    return InventorySummary(
        active_item_count=len(items),
        total_quantity_on_hand=total_on_hand,
        low_stock_item_count=low_stock_count,
    )


def _warehouse_summary(db: Session, user: User, plant_id: str | None) -> WarehouseSummary:
    putaway_query = db.query(PutawayTask).filter(
        PutawayTask.tenant_id == user.tenant_id, PutawayTask.status == TaskStatus.pending
    )
    pick_query = db.query(PickTask).filter(PickTask.tenant_id == user.tenant_id, PickTask.status == TaskStatus.pending)
    if plant_id:
        putaway_query = putaway_query.filter(PutawayTask.plant_id == plant_id)
        pick_query = pick_query.filter(PickTask.plant_id == plant_id)

    return WarehouseSummary(
        pending_putaway_tasks=putaway_query.count(),
        pending_pick_tasks=pick_query.count(),
    )


def _production_summary(db: Session, user: User, plant_id: str | None) -> ProductionSummary:
    query = db.query(ProductionOrder).filter(ProductionOrder.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(ProductionOrder.plant_id == plant_id)
    orders = query.all()

    return ProductionSummary(
        open_orders=sum(1 for o in orders if o.status == ProductionOrderStatus.planned),
        in_progress_orders=sum(1 for o in orders if o.status == ProductionOrderStatus.in_progress),
        completed_orders=sum(1 for o in orders if o.status == ProductionOrderStatus.completed),
        total_quantity_completed=sum((o.quantity_completed for o in orders), Decimal("0")),
    )


def _procurement_summary(db: Session, user: User, plant_id: str | None) -> ProcurementSummary:
    query = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == user.tenant_id,
        PurchaseOrder.status.in_([PurchaseOrderStatus.submitted, PurchaseOrderStatus.partially_received]),
    )
    if plant_id:
        query = query.filter(PurchaseOrder.plant_id == plant_id)
    open_orders = query.all()

    outstanding = Decimal("0")
    if open_orders:
        order_ids = [o.id for o in open_orders]
        for line in db.query(PurchaseOrderLine).filter(PurchaseOrderLine.order_id.in_(order_ids)).all():
            outstanding += line.quantity_ordered - line.quantity_received

    return ProcurementSummary(open_purchase_orders=len(open_orders), outstanding_quantity_ordered=outstanding)


def _sales_summary(db: Session, user: User, plant_id: str | None) -> SalesSummary:
    query = db.query(SalesOrder).filter(
        SalesOrder.tenant_id == user.tenant_id,
        SalesOrder.status.in_([SalesOrderStatus.confirmed, SalesOrderStatus.partially_shipped]),
    )
    if plant_id:
        query = query.filter(SalesOrder.plant_id == plant_id)
    open_orders = query.all()

    outstanding = Decimal("0")
    if open_orders:
        order_ids = [o.id for o in open_orders]
        for line in db.query(SalesOrderLine).filter(SalesOrderLine.order_id.in_(order_ids)).all():
            outstanding += line.quantity_ordered - line.quantity_shipped

    return SalesSummary(open_sales_orders=len(open_orders), outstanding_quantity_to_ship=outstanding)


def _maintenance_summary(db: Session, user: User, plant_id: str | None) -> MaintenanceSummary:
    wo_query = db.query(MaintenanceWorkOrder).filter(
        MaintenanceWorkOrder.tenant_id == user.tenant_id,
        MaintenanceWorkOrder.status.in_([WorkOrderStatus.open, WorkOrderStatus.in_progress]),
    )
    asset_query = db.query(Asset).filter(
        Asset.tenant_id == user.tenant_id,
        Asset.status.in_([AssetStatus.down, AssetStatus.maintenance]),
    )
    if plant_id:
        wo_query = wo_query.filter(MaintenanceWorkOrder.plant_id == plant_id)
        asset_query = asset_query.filter(Asset.plant_id == plant_id)

    return MaintenanceSummary(
        open_work_orders=wo_query.count(),
        assets_down_or_in_maintenance=asset_query.count(),
    )


def _quality_summary(db: Session, user: User, plant_id: str | None) -> QualitySummary:
    inspection_query = db.query(Inspection).filter(Inspection.tenant_id == user.tenant_id)
    if plant_id:
        inspection_query = inspection_query.filter(Inspection.plant_id == plant_id)
    total = inspection_query.count()
    failed = inspection_query.filter(Inspection.result == InspectionResult.fail).count()

    open_defects = (
        db.query(func.count(Defect.id))
        .join(Inspection, Defect.inspection_id == Inspection.id)
        .filter(Inspection.tenant_id == user.tenant_id, Defect.status == DefectStatus.open)
    )
    if plant_id:
        open_defects = open_defects.filter(Inspection.plant_id == plant_id)

    return QualitySummary(
        total_inspections=total,
        failed_inspections=failed,
        open_defects=open_defects.scalar() or 0,
    )


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    plant_id: str | None = None,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> DashboardOut:
    return DashboardOut(
        inventory=_inventory_summary(db, user, plant_id),
        warehouse=_warehouse_summary(db, user, plant_id),
        production=_production_summary(db, user, plant_id),
        procurement=_procurement_summary(db, user, plant_id),
        sales=_sales_summary(db, user, plant_id),
        maintenance=_maintenance_summary(db, user, plant_id),
        quality=_quality_summary(db, user, plant_id),
    )
