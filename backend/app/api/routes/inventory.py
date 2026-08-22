from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.inventory import Item, MovementType, StockBalance, StockMovement
from app.models.tenant import Plant
from app.models.user import User
from app.schemas.inventory import (
    ItemCreate,
    ItemOut,
    ItemUpdate,
    StockBalanceOut,
    StockMovementCreate,
    StockMovementOut,
)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

_NEGATIVE_MOVEMENTS = {MovementType.issue, MovementType.transfer_out}
_POSITIVE_MOVEMENTS = {MovementType.receipt, MovementType.transfer_in}


def _get_owned_item(db: Session, user: User, item_id: str) -> Item:
    item = db.get(Item, item_id)
    if item is None or item.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


def _get_owned_plant(db: Session, user: User, plant_id: str) -> Plant:
    plant = db.get(Plant, plant_id)
    if plant is None or plant.company.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return plant


@router.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    existing = db.query(Item).filter(Item.tenant_id == user.tenant_id, Item.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    item = Item(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/items", response_model=list[ItemOut])
def list_items(
    active_only: bool = True,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Item).filter(Item.tenant_id == user.tenant_id)
    if active_only:
        query = query.filter(Item.is_active.is_(True))
    return query.order_by(Item.sku).all()


@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    return _get_owned_item(db, user, item_id)


@router.patch("/items/{item_id}", response_model=ItemOut)
def update_item(
    item_id: str,
    payload: ItemUpdate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    item = _get_owned_item(db, user, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.get("/balances", response_model=list[StockBalanceOut])
def list_balances(
    plant_id: str | None = None,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(StockBalance).filter(StockBalance.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(StockBalance.plant_id == plant_id)

    results = []
    for balance in query.all():
        results.append(
            StockBalanceOut(
                id=balance.id,
                plant_id=balance.plant_id,
                item_id=balance.item_id,
                item_sku=balance.item.sku,
                item_name=balance.item.name,
                quantity_on_hand=balance.quantity_on_hand,
                quantity_reserved=balance.quantity_reserved,
                quantity_available=balance.quantity_on_hand - balance.quantity_reserved,
            )
        )
    return results


@router.post("/movements", response_model=StockMovementOut, status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    if payload.quantity == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Quantity cannot be zero")

    item = _get_owned_item(db, user, payload.item_id)
    _get_owned_plant(db, user, payload.plant_id)

    if payload.movement_type != MovementType.adjustment and payload.quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Quantity must be positive for this movement type",
        )

    if payload.movement_type in _NEGATIVE_MOVEMENTS:
        delta = -payload.quantity
    elif payload.movement_type in _POSITIVE_MOVEMENTS:
        delta = payload.quantity
    else:
        delta = payload.quantity

    balance = (
        db.query(StockBalance)
        .filter(StockBalance.plant_id == payload.plant_id, StockBalance.item_id == payload.item_id)
        .first()
    )
    if balance is None:
        balance = StockBalance(
            tenant_id=user.tenant_id,
            plant_id=payload.plant_id,
            item_id=payload.item_id,
            quantity_on_hand=Decimal("0"),
            quantity_reserved=Decimal("0"),
        )
        db.add(balance)
        db.flush()

    new_on_hand = balance.quantity_on_hand + delta
    if new_on_hand < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Movement would result in negative stock on hand",
        )
    balance.quantity_on_hand = new_on_hand

    movement = StockMovement(
        tenant_id=user.tenant_id,
        plant_id=payload.plant_id,
        item_id=item.id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        reference=payload.reference,
        notes=payload.notes,
        created_by_user_id=user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/movements", response_model=list[StockMovementOut])
def list_movements(
    plant_id: str | None = None,
    item_id: str | None = None,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(StockMovement).filter(StockMovement.tenant_id == user.tenant_id)
    if plant_id:
        query = query.filter(StockMovement.plant_id == plant_id)
    if item_id:
        query = query.filter(StockMovement.item_id == item_id)
    return query.order_by(StockMovement.created_at.desc()).all()
