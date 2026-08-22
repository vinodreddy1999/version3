from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routes.inventory import _get_owned_plant
from app.models.maintenance import Asset, AssetStatus, MaintenanceWorkOrder, WorkOrderStatus
from app.models.user import User
from app.schemas.maintenance import AssetCreate, AssetOut, WorkOrderCreate, WorkOrderOut

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    _get_owned_plant(db, user, payload.plant_id)
    existing = db.query(Asset).filter(Asset.plant_id == payload.plant_id, Asset.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset code already exists for this plant")

    asset = Asset(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    plant_id: str | None = None, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    query = db.query(Asset).filter(Asset.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(Asset.plant_id == plant_id)
    return query.order_by(Asset.name).all()


def _get_owned_asset(db: Session, user: User, asset_id: str) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


def _get_owned_work_order(db: Session, user: User, work_order_id: str) -> MaintenanceWorkOrder:
    order = db.get(MaintenanceWorkOrder, work_order_id)
    if order is None or order.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return order


@router.post("/work-orders", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
def create_work_order(
    payload: WorkOrderCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_asset(db, user, payload.asset_id)

    work_order = MaintenanceWorkOrder(tenant_id=user.tenant_id, created_by_user_id=user.id, **payload.model_dump())
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@router.get("/work-orders", response_model=list[WorkOrderOut])
def list_work_orders(
    plant_id: str | None = None,
    asset_id: str | None = None,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(MaintenanceWorkOrder.plant_id == plant_id)
    if asset_id:
        query = query.filter(MaintenanceWorkOrder.asset_id == asset_id)
    return query.order_by(MaintenanceWorkOrder.created_at.desc()).all()


@router.post("/work-orders/{work_order_id}/start", response_model=WorkOrderOut)
def start_work_order(
    work_order_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    order = _get_owned_work_order(db, user, work_order_id)
    if order.status != WorkOrderStatus.open:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only open work orders can be started")

    order.status = WorkOrderStatus.in_progress
    order.asset.status = AssetStatus.maintenance
    db.commit()
    db.refresh(order)
    return order


@router.post("/work-orders/{work_order_id}/complete", response_model=WorkOrderOut)
def complete_work_order(
    work_order_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    order = _get_owned_work_order(db, user, work_order_id)
    if order.status != WorkOrderStatus.in_progress:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only in-progress work orders can be completed")

    order.status = WorkOrderStatus.completed
    order.asset.status = AssetStatus.operational
    db.commit()
    db.refresh(order)
    return order


@router.post("/work-orders/{work_order_id}/cancel", response_model=WorkOrderOut)
def cancel_work_order(
    work_order_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    order = _get_owned_work_order(db, user, work_order_id)
    if order.status not in (WorkOrderStatus.open, WorkOrderStatus.in_progress):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Work order cannot be cancelled in its current state")

    was_in_progress = order.status == WorkOrderStatus.in_progress
    order.status = WorkOrderStatus.cancelled
    if was_in_progress:
        order.asset.status = AssetStatus.operational
    db.commit()
    db.refresh(order)
    return order
