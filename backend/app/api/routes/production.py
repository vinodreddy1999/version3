from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import PaginationParams, get_current_user, get_db_session, get_owned
from app.api.routes.inventory import _get_owned_item, _get_owned_plant
from app.core.csv_export import csv_response
from app.models.inventory import Item, MovementType, StockBalance, StockMovement
from app.models.production import (
    BillOfMaterial,
    BOMComponent,
    ProductionOrder,
    ProductionOrderStatus,
    WorkCenter,
)
from app.models.user import User
from app.schemas.production import (
    BOMCreate,
    BOMOut,
    ProductionOrderCompleteRequest,
    ProductionOrderCreate,
    ProductionOrderOut,
    WorkCenterCreate,
    WorkCenterOut,
)

router = APIRouter(prefix="/api/production", tags=["production"])


@router.post("/work-centers", response_model=WorkCenterOut, status_code=status.HTTP_201_CREATED)
def create_work_center(
    payload: WorkCenterCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    if db.query(WorkCenter).filter(WorkCenter.plant_id == payload.plant_id, WorkCenter.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Work center code already exists")

    work_center = WorkCenter(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(work_center)
    db.commit()
    db.refresh(work_center)
    return work_center


@router.get("/work-centers", response_model=list[WorkCenterOut])
def list_work_centers(
    response: Response,
    plant_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(WorkCenter).filter(WorkCenter.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(WorkCenter.plant_id == plant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(WorkCenter.name).offset(pagination.offset).limit(pagination.limit).all()


def _bom_to_out(bom: BillOfMaterial) -> BOMOut:
    return BOMOut(
        id=bom.id,
        output_item_id=bom.output_item_id,
        name=bom.name,
        version=bom.version,
        is_active=bom.is_active,
        components=[
            {
                "component_item_id": c.component_item_id,
                "component_sku": c.component_item.sku,
                "quantity_per_unit": c.quantity_per_unit,
            }
            for c in bom.components
        ],
    )


@router.post("/boms", response_model=BOMOut, status_code=status.HTTP_201_CREATED)
def create_bom(payload: BOMCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    output_item = _get_owned_item(db, user, payload.output_item_id)

    for component in payload.components:
        _get_owned_item(db, user, component.component_item_id)
        if component.component_item_id == output_item.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="A component cannot be the BOM's own output item"
            )

    if (
        db.query(BillOfMaterial)
        .filter(
            BillOfMaterial.tenant_id == user.tenant_id,
            BillOfMaterial.output_item_id == output_item.id,
            BillOfMaterial.version == payload.version,
        )
        .first()
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A BOM with this output item and version already exists")

    bom = BillOfMaterial(
        tenant_id=user.tenant_id,
        output_item_id=output_item.id,
        name=payload.name,
        version=payload.version,
    )
    bom.components = [
        BOMComponent(component_item_id=c.component_item_id, quantity_per_unit=c.quantity_per_unit)
        for c in payload.components
    ]
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return _bom_to_out(bom)


@router.get("/boms", response_model=list[BOMOut])
def list_boms(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    base_query = db.query(BillOfMaterial).filter(BillOfMaterial.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(base_query.count())
    boms = (
        base_query.options(joinedload(BillOfMaterial.components).joinedload(BOMComponent.component_item))
        .order_by(BillOfMaterial.name)
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )
    return [_bom_to_out(b) for b in boms]


def _get_owned_bom(db: Session, user: User, bom_id: str) -> BillOfMaterial:
    return get_owned(db, BillOfMaterial, bom_id, user, "BOM")


@router.post("/orders", response_model=ProductionOrderOut, status_code=status.HTTP_201_CREATED)
def create_production_order(
    payload: ProductionOrderCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    bom = _get_owned_bom(db, user, payload.bom_id)
    if not bom.is_active:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="BOM is not active")

    order = ProductionOrder(
        tenant_id=user.tenant_id,
        created_by_user_id=user.id,
        **payload.model_dump(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=list[ProductionOrderOut])
def list_production_orders(
    response: Response,
    plant_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(ProductionOrder).filter(ProductionOrder.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(ProductionOrder.plant_id == plant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return (
        query.order_by(ProductionOrder.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )


@router.get("/orders/export")
def export_production_orders(
    plant_id: str | None = None, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    query = db.query(ProductionOrder).options(joinedload(ProductionOrder.bom)).filter(
        ProductionOrder.tenant_id == user.tenant_id
    )
    if plant_id:
        query = query.filter(ProductionOrder.plant_id == plant_id)
    orders = query.order_by(ProductionOrder.created_at.desc()).all()

    rows = []
    for order in orders:
        output_item = db.get(Item, order.bom.output_item_id)
        rows.append(
            [
                order.id,
                output_item.sku if output_item else "",
                order.status.value,
                str(order.quantity_planned),
                str(order.quantity_completed),
                order.created_at.isoformat(),
            ]
        )
    return csv_response(
        "production_orders.csv",
        ["Order ID", "Output SKU", "Status", "Planned", "Completed", "Created"],
        rows,
    )


@router.post("/orders/{order_id}/complete", response_model=ProductionOrderOut)
def complete_production_order(
    order_id: str,
    payload: ProductionOrderCompleteRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    order = (
        db.query(ProductionOrder)
        .options(joinedload(ProductionOrder.bom).joinedload(BillOfMaterial.components))
        .filter(ProductionOrder.id == order_id, ProductionOrder.tenant_id == user.tenant_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production order not found")
    if order.status not in (ProductionOrderStatus.planned, ProductionOrderStatus.in_progress):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is not open for completion")

    remaining = order.quantity_planned - order.quantity_completed
    if payload.quantity > remaining:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Quantity exceeds remaining planned quantity ({remaining})",
        )

    balances_by_item: dict[str, StockBalance] = {}
    for component in order.bom.components:
        required = component.quantity_per_unit * payload.quantity
        balance = (
            db.query(StockBalance)
            .filter(StockBalance.plant_id == order.plant_id, StockBalance.item_id == component.component_item_id)
            .first()
        )
        if balance is None or balance.quantity_on_hand < required:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Insufficient stock for component {component.component_item_id}",
            )
        balances_by_item[component.component_item_id] = balance

    for component in order.bom.components:
        required = component.quantity_per_unit * payload.quantity
        balance = balances_by_item[component.component_item_id]
        balance.quantity_on_hand -= required
        db.add(
            StockMovement(
                tenant_id=user.tenant_id,
                plant_id=order.plant_id,
                item_id=component.component_item_id,
                movement_type=MovementType.issue,
                quantity=required,
                reference=f"production-order:{order.id}",
                created_by_user_id=user.id,
            )
        )

    output_balance = (
        db.query(StockBalance)
        .filter(StockBalance.plant_id == order.plant_id, StockBalance.item_id == order.bom.output_item_id)
        .first()
    )
    if output_balance is None:
        output_balance = StockBalance(
            tenant_id=user.tenant_id,
            plant_id=order.plant_id,
            item_id=order.bom.output_item_id,
            quantity_on_hand=Decimal("0"),
            quantity_reserved=Decimal("0"),
        )
        db.add(output_balance)
        db.flush()
    output_balance.quantity_on_hand += payload.quantity
    db.add(
        StockMovement(
            tenant_id=user.tenant_id,
            plant_id=order.plant_id,
            item_id=order.bom.output_item_id,
            movement_type=MovementType.receipt,
            quantity=payload.quantity,
            reference=f"production-order:{order.id}",
            created_by_user_id=user.id,
        )
    )

    order.quantity_completed += payload.quantity
    order.status = (
        ProductionOrderStatus.completed
        if order.quantity_completed >= order.quantity_planned
        else ProductionOrderStatus.in_progress
    )
    db.commit()
    db.refresh(order)
    return order
