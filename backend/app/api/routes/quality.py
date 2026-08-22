from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db_session
from app.api.routes.inventory import _get_owned_item, _get_owned_plant
from app.models.quality import Defect, DefectStatus, Inspection, InspectionResult
from app.models.user import User
from app.schemas.quality import InspectionCreate, InspectionOut

router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.post("/inspections", response_model=InspectionOut, status_code=status.HTTP_201_CREATED)
def create_inspection(
    payload: InspectionCreate, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    _get_owned_plant(db, user, payload.plant_id)
    _get_owned_item(db, user, payload.item_id)

    inspection = Inspection(
        tenant_id=user.tenant_id,
        plant_id=payload.plant_id,
        item_id=payload.item_id,
        reference=payload.reference,
        inspected_quantity=payload.inspected_quantity,
        notes=payload.notes,
        inspector_user_id=user.id,
        result=InspectionResult.fail if payload.defects else InspectionResult.pass_,
    )
    inspection.defects = [
        Defect(
            tenant_id=user.tenant_id,
            defect_type=d.defect_type,
            severity=d.severity,
            quantity=d.quantity,
            description=d.description,
        )
        for d in payload.defects
    ]
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("/inspections", response_model=list[InspectionOut])
def list_inspections(
    plant_id: str | None = None,
    result: InspectionResult | None = None,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = (
        db.query(Inspection)
        .options(joinedload(Inspection.defects))
        .filter(Inspection.tenant_id == user.tenant_id)
    )
    if plant_id:
        query = query.filter(Inspection.plant_id == plant_id)
    if result:
        query = query.filter(Inspection.result == result)
    return query.order_by(Inspection.created_at.desc()).all()


@router.post("/defects/{defect_id}/resolve", response_model=InspectionOut)
def resolve_defect(defect_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)):
    defect = db.get(Defect, defect_id)
    if defect is None or defect.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Defect not found")
    if defect.status == DefectStatus.resolved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Defect already resolved")

    defect.status = DefectStatus.resolved
    db.commit()
    db.refresh(defect.inspection)
    return defect.inspection
