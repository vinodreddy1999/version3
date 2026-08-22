from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_current_user, get_db_session
from app.models.tenant import Company, Plant
from app.models.user import User
from app.schemas.org import CompanyCreate, CompanyOut, PlantCreate, PlantOut

router = APIRouter(prefix="/api/org", tags=["organization"])


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    existing = db.query(Company).filter(Company.tenant_id == user.tenant_id, Company.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company code already exists")

    company = Company(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Company).filter(Company.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Company.name).offset(pagination.offset).limit(pagination.limit).all()


def _get_owned_company(db: Session, user: User, company_id: str) -> Company:
    company = db.get(Company, company_id)
    if company is None or company.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.post("/plants", response_model=PlantOut, status_code=status.HTTP_201_CREATED)
def create_plant(
    payload: PlantCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    company = _get_owned_company(db, user, payload.company_id)
    existing = db.query(Plant).filter(Plant.company_id == company.id, Plant.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Plant code already exists for this company")

    plant = Plant(**payload.model_dump())
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("/plants", response_model=list[PlantOut])
def list_plants(
    response: Response,
    company_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    query = db.query(Plant).join(Company).filter(Company.tenant_id == user.tenant_id)
    if company_id:
        query = query.filter(Plant.company_id == company_id)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(Plant.name).offset(pagination.offset).limit(pagination.limit).all()
