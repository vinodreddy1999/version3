from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import PaginationParams, get_current_user, get_db_session, get_owned
from app.api.routes.inventory import _get_owned_item, _get_owned_plant
from app.core.csv_export import csv_response
from app.models.inventory import MovementType, StockBalance, StockMovement
from app.models.sales import Customer, SalesOrder, SalesOrderLine, SalesOrderStatus
from app.models.user import User
from app.schemas.sales import CustomerCreate, CustomerOut, SalesOrderCreate, SalesOrderOut, ShipLineRequest

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    if db.query(Customer).filter(Customer.tenant_id == user.tenant_id, Customer.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer code already exists")

    customer = Customer(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Customer).filter(Customer.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Customer.name).offset(pagination.offset).limit(pagination.limit).all()


def _get_owned_customer(db: Session, user: User, customer_id: str) -> Customer:
    return get_owned(db, Customer, customer_id, user, "Customer")


def _get_owned_so(db: Session, user: User, order_id: str) -> SalesOrder:
    order = (
        db.query(SalesOrder)
        .options(joinedload(SalesOrder.lines))
        .filter(SalesOrder.id == order_id, SalesOrder.tenant_id == user.tenant_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
    return order


@router.post("/orders", response_model=SalesOrderOut, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    payload: SalesOrderCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_customer(db, user, payload.customer_id)
    for line in payload.lines:
        _get_owned_item(db, user, line.item_id)

    order = SalesOrder(
        tenant_id=user.tenant_id,
        plant_id=payload.plant_id,
        customer_id=payload.customer_id,
        reference=payload.reference,
        created_by_user_id=user.id,
    )
    order.lines = [
        SalesOrderLine(item_id=line.item_id, quantity_ordered=line.quantity_ordered, unit_price=line.unit_price)
        for line in payload.lines
    ]
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders", response_model=list[SalesOrderOut])
def list_sales_orders(
    response: Response,
    plant_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    base_query = db.query(SalesOrder).filter(SalesOrder.tenant_id == user.tenant_id)
    if plant_id:
        base_query = base_query.filter(SalesOrder.plant_id == plant_id)
    response.headers["X-Total-Count"] = str(base_query.count())
    return (
        base_query.options(joinedload(SalesOrder.lines))
        .order_by(SalesOrder.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )


@router.get("/orders/export")
def export_sales_orders(
    plant_id: str | None = None, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    query = db.query(SalesOrder).options(joinedload(SalesOrder.lines)).filter(
        SalesOrder.tenant_id == user.tenant_id
    )
    if plant_id:
        query = query.filter(SalesOrder.plant_id == plant_id)
    orders = query.order_by(SalesOrder.created_at.desc()).all()

    rows = []
    for order in orders:
        customer = db.get(Customer, order.customer_id)
        for line in order.lines:
            rows.append(
                [
                    order.reference or order.id,
                    customer.name if customer else "",
                    order.status.value,
                    line.item.sku,
                    str(line.quantity_ordered),
                    str(line.quantity_shipped),
                    str(line.unit_price),
                ]
            )
    return csv_response(
        "sales_orders.csv",
        ["Reference", "Customer", "Status", "SKU", "Ordered", "Shipped", "Unit Price"],
        rows,
    )


@router.post("/orders/{order_id}/confirm", response_model=SalesOrderOut)
def confirm_sales_order(order_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    order = _get_owned_so(db, user, order_id)
    if order.status != SalesOrderStatus.draft:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft orders can be confirmed")
    order.status = SalesOrderStatus.confirmed
    db.commit()
    db.refresh(order)
    return order


@router.post("/orders/{order_id}/ship", response_model=SalesOrderOut)
def ship_sales_order_line(
    order_id: str,
    payload: ShipLineRequest,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    order = _get_owned_so(db, user, order_id)
    if order.status not in (SalesOrderStatus.confirmed, SalesOrderStatus.partially_shipped):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is not open for shipping")

    line = next((ln for ln in order.lines if ln.id == payload.line_id), None)
    if line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")

    remaining = line.quantity_ordered - line.quantity_shipped
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
    if balance is None or balance.quantity_on_hand < payload.quantity:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Insufficient stock to ship")

    balance.quantity_on_hand -= payload.quantity
    line.quantity_shipped += payload.quantity

    db.add(
        StockMovement(
            tenant_id=user.tenant_id,
            plant_id=order.plant_id,
            item_id=line.item_id,
            movement_type=MovementType.issue,
            quantity=payload.quantity,
            reference=f"sales-order:{order.id}",
            created_by_user_id=user.id,
        )
    )

    all_shipped = all(ln.quantity_shipped >= ln.quantity_ordered for ln in order.lines)
    order.status = SalesOrderStatus.shipped if all_shipped else SalesOrderStatus.partially_shipped

    db.commit()
    db.refresh(order)
    return order
