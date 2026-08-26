from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_current_user, get_db_session, get_owned
from app.api.routes.inventory import _get_owned_item, _get_owned_plant
from app.models.inventory import MovementType, StockBalance, StockMovement
from app.models.user import User
from app.models.warehouse import Bin, BinStock, PickTask, PutawayTask, TaskStatus, Warehouse, Zone
from app.schemas.warehouse import (
    BinCreate,
    BinOut,
    BinStockOut,
    PickTaskCreate,
    PickTaskOut,
    PutawayTaskCreate,
    PutawayTaskOut,
    WarehouseCreate,
    WarehouseOut,
    ZoneCreate,
    ZoneOut,
)

router = APIRouter(prefix="/api/warehouse", tags=["warehouse"])


def _get_owned_warehouse(db: Session, user: User, warehouse_id: str) -> Warehouse:
    return get_owned(db, Warehouse, warehouse_id, user, "Warehouse")


def _get_owned_zone(db: Session, user: User, zone_id: str) -> Zone:
    zone = db.get(Zone, zone_id)
    if zone is None or zone.warehouse.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone


def _get_owned_bin(db: Session, user: User, bin_id: str) -> Bin:
    bin_ = db.get(Bin, bin_id)
    if bin_ is None or bin_.zone.warehouse.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bin not found")
    return bin_


@router.post("/warehouses", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    existing = (
        db.query(Warehouse)
        .filter(Warehouse.plant_id == payload.plant_id, Warehouse.code == payload.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse code already exists for this plant")

    warehouse = Warehouse(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(
    response: Response,
    plant_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Warehouse).filter(Warehouse.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(Warehouse.plant_id == plant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Warehouse.name).offset(pagination.offset).limit(pagination.limit).all()


@router.post("/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    warehouse = _get_owned_warehouse(db, user, payload.warehouse_id)
    if db.query(Zone).filter(Zone.warehouse_id == warehouse.id, Zone.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Zone code already exists for this warehouse")

    zone = Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/zones", response_model=list[ZoneOut])
def list_zones(
    response: Response,
    warehouse_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Zone).join(Warehouse).filter(Warehouse.tenant_id == user.tenant_id)
    if warehouse_id:
        query = query.filter(Zone.warehouse_id == warehouse_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Zone.name).offset(pagination.offset).limit(pagination.limit).all()


@router.post("/bins", response_model=BinOut, status_code=status.HTTP_201_CREATED)
def create_bin(payload: BinCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    zone = _get_owned_zone(db, user, payload.zone_id)
    if db.query(Bin).filter(Bin.zone_id == zone.id, Bin.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bin code already exists in this zone")

    bin_ = Bin(**payload.model_dump())
    db.add(bin_)
    db.commit()
    db.refresh(bin_)
    return bin_


@router.get("/bins", response_model=list[BinOut])
def list_bins(
    response: Response,
    zone_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Bin).join(Zone).join(Warehouse).filter(Warehouse.tenant_id == user.tenant_id)
    if zone_id:
        query = query.filter(Bin.zone_id == zone_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Bin.code).offset(pagination.offset).limit(pagination.limit).all()


@router.get("/bin-stock", response_model=list[BinStockOut])
def list_bin_stock(
    response: Response,
    warehouse_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(BinStock).filter(BinStock.tenant_id == user.tenant_id)
    if warehouse_id:
        query = query.join(Bin).join(Zone).filter(Zone.warehouse_id == warehouse_id)
    response.headers["X-Total-Count"] = str(query.count())
    return [
        BinStockOut(
            bin_id=row.bin_id,
            bin_code=row.bin.code,
            item_id=row.item_id,
            item_sku=row.item.sku,
            quantity=row.quantity,
        )
        for row in query.offset(pagination.offset).limit(pagination.limit).all()
    ]


@router.post("/putaway-tasks", response_model=PutawayTaskOut, status_code=status.HTTP_201_CREATED)
def create_putaway_task(
    payload: PutawayTaskCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_item(db, user, payload.item_id)
    _get_owned_bin(db, user, payload.destination_bin_id)

    task = PutawayTask(tenant_id=user.tenant_id, created_by_user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.post("/putaway-tasks/{task_id}/complete", response_model=PutawayTaskOut)
def complete_putaway_task(
    task_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    task = db.get(PutawayTask, task_id)
    if task is None or task.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Putaway task not found")
    if task.status != TaskStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is not pending")

    bin_stock = (
        db.query(BinStock)
        .filter(BinStock.bin_id == task.destination_bin_id, BinStock.item_id == task.item_id)
        .first()
    )
    if bin_stock is None:
        bin_stock = BinStock(
            tenant_id=user.tenant_id,
            bin_id=task.destination_bin_id,
            item_id=task.item_id,
            quantity=Decimal("0"),
        )
        db.add(bin_stock)
        db.flush()
    bin_stock.quantity += task.quantity
    task.status = TaskStatus.completed
    db.commit()
    db.refresh(task)
    return task


@router.post("/pick-tasks", response_model=PickTaskOut, status_code=status.HTTP_201_CREATED)
def create_pick_task(
    payload: PickTaskCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_item(db, user, payload.item_id)
    _get_owned_bin(db, user, payload.source_bin_id)

    task = PickTask(tenant_id=user.tenant_id, created_by_user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.post("/pick-tasks/{task_id}/complete", response_model=PickTaskOut)
def complete_pick_task(task_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    task = db.get(PickTask, task_id)
    if task is None or task.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick task not found")
    if task.status != TaskStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is not pending")

    bin_stock = (
        db.query(BinStock).filter(BinStock.bin_id == task.source_bin_id, BinStock.item_id == task.item_id).first()
    )
    if bin_stock is None or bin_stock.quantity < task.quantity:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Insufficient bin stock")

    balance = (
        db.query(StockBalance)
        .filter(StockBalance.plant_id == task.plant_id, StockBalance.item_id == task.item_id)
        .first()
    )
    if balance is None or balance.quantity_on_hand < task.quantity:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Insufficient plant stock")

    bin_stock.quantity -= task.quantity
    balance.quantity_on_hand -= task.quantity
    db.add(
        StockMovement(
            tenant_id=user.tenant_id,
            plant_id=task.plant_id,
            item_id=task.item_id,
            movement_type=MovementType.issue,
            quantity=task.quantity,
            reference=task.reference or f"pick-task:{task.id}",
            created_by_user_id=user.id,
        )
    )
    task.status = TaskStatus.completed
    db.commit()
    db.refresh(task)
    return task
