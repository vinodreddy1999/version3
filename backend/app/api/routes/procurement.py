from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import PaginationParams, get_current_user, get_db_session
from app.api.routes.inventory import _get_owned_item, _get_owned_plant
from app.core.csv_export import csv_response
from app.models.inventory import MovementType, StockBalance, StockMovement
from app.models.procurement import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus, Supplier
from app.models.user import User
from app.schemas.procurement import (
    PurchaseOrderCreate,
    PurchaseOrderOut,
    ReceiveLineRequest,
    SupplierCreate,
    SupplierOut,
)

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


@router.post("/suppliers", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    existing = db.query(Supplier).filter(Supplier.tenant_id == user.tenant_id, Supplier.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier code already exists")

    supplier = Supplier(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Supplier).filter(Supplier.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Supplier.name).offset(pagination.offset).limit(pagination.limit).all()


def _get_owned_supplier(db: Session, user: User, supplier_id: str) -> Supplier:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None or supplier.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier


def _get_owned_po(db: Session, user: User, order_id: str) -> PurchaseOrder:
    order = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.lines))
        .filter(PurchaseOrder.id == order_id, PurchaseOrder.tenant_id == user.tenant_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return order


@router.post("/orders", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_supplier(db, user, payload.supplier_id)
    for line in payload.lines:
        _get_owned_item(db, user, line.item_id)

    order = PurchaseOrder(
        tenant_id=user.tenant_id,
        plant_id=payload.plant_id,
        supplier_id=payload.supplier_id,
        reference=payload.reference,
        created_by_user_id=user.id,
    )
    order.lines = [
        PurchaseOrderLine(item_id=line.item_id, quantity_ordered=line.quantity_ordered, unit_price=line.unit_price)
        for line in payload.lines
    ]
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    response: Response,
    plant_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    base_query = db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == user.tenant_id)
    if plant_id:
        base_query = base_query.filter(PurchaseOrder.plant_id == plant_id)
    response.headers["X-Total-Count"] = str(base_query.count())
    return (
        base_query.options(joinedload(PurchaseOrder.lines))
        .order_by(PurchaseOrder.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )


@router.get("/orders/export")
def export_purchase_orders(
    plant_id: str | None = None, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    query = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.lines)).filter(
        PurchaseOrder.tenant_id == user.tenant_id
    )
    if plant_id:
        query = query.filter(PurchaseOrder.plant_id == plant_id)
    orders = query.order_by(PurchaseOrder.created_at.desc()).all()

    rows = []
    for order in orders:
        supplier = db.get(Supplier, order.supplier_id)
        for line in order.lines:
            rows.append(
                [
                    order.reference or order.id,
                    supplier.name if supplier else "",
                    order.status.value,
                    line.item.sku,
                    str(line.quantity_ordered),
                    str(line.quantity_received),
                    str(line.unit_price),
                ]
            )
    return csv_response(
        "purchase_orders.csv",
        ["Reference", "Supplier", "Status", "SKU", "Ordered", "Received", "Unit Price"],
        rows,
    )


@router.post("/orders/{order_id}/submit", response_model=PurchaseOrderOut)
def submit_purchase_order(order_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    order = _get_owned_po(db, user, order_id)
    if order.status != PurchaseOrderStatus.draft:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft orders can be submitted")
    order.status = PurchaseOrderStatus.submitted
    db.commit()
    db.refresh(order)
    return order


@router.post("/orders/{order_id}/receive", response_model=PurchaseOrderOut)
def receive_purchase_order_line(
    order_id: str,
    payload: ReceiveLineRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    order = _get_owned_po(db, user, order_id)
    if order.status not in (PurchaseOrderStatus.submitted, PurchaseOrderStatus.partially_received):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is not open for receiving")

    line = next((ln for ln in order.lines if ln.id == payload.line_id), None)
    if line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")

    remaining = line.quantity_ordered - line.quantity_received
    if payload.quantity > remaining:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Quantity exceeds remaining ordered quantity ({remaining})",
        )

    balance = (
        db.query(StockBalance)
        .filter(StockBalance.plant_id == order.plant_id, StockBalance.item_id == line.item_id)
        .first()
    )
    if balance is None:
        balance = StockBalance(tenant_id=user.tenant_id, plant_id=order.plant_id, item_id=line.item_id)
        db.add(balance)
        db.flush()
    balance.quantity_on_hand += payload.quantity
    line.quantity_received += payload.quantity

    db.add(
        StockMovement(
            tenant_id=user.tenant_id,
            plant_id=order.plant_id,
            item_id=line.item_id,
            movement_type=MovementType.receipt,
            quantity=payload.quantity,
            reference=f"purchase-order:{order.id}",
            created_by_user_id=user.id,
        )
    )

    all_received = all(ln.quantity_received >= ln.quantity_ordered for ln in order.lines)
    order.status = PurchaseOrderStatus.received if all_received else PurchaseOrderStatus.partially_received

    db.commit()
    db.refresh(order)
    return order
