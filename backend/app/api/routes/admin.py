from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload

from app.api.deps import PaginationParams, get_current_user, get_db_session, require_permissions
from app.core.audit import record_audit
from app.core.permissions import PERMISSION_CODES
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.user import Permission, Role, User
from app.schemas.admin import (
    AuditLogOut,
    PermissionOut,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    UserAdminOut,
    UserCreate,
    UserUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _role_to_out(role: Role) -> RoleOut:
    return RoleOut(
        id=role.id,
        name=role.name,
        is_system=role.is_system,
        permission_codes=sorted(p.code for p in role.permissions),
    )


def _user_to_out(user: User) -> UserAdminOut:
    return UserAdminOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role_ids=[r.id for r in user.roles],
        role_names=[r.name for r in user.roles],
    )


def _audit_to_out(entry: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        id=entry.id,
        action=entry.action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        summary=entry.summary,
        actor_email=entry.actor.email if entry.actor else None,
        created_at=entry.created_at,
    )


def _resolve_permissions(db: Session, codes: list[str]) -> list[Permission]:
    unknown = set(codes) - PERMISSION_CODES
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown permission code(s): {', '.join(sorted(unknown))}",
        )
    if not codes:
        return []
    return db.query(Permission).filter(Permission.code.in_(codes)).all()


def _resolve_roles(db: Session, user: User, role_ids: list[str]) -> list[Role]:
    if not role_ids:
        return []
    roles = db.query(Role).filter(Role.id.in_(role_ids), Role.tenant_id == user.tenant_id).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="One or more roles not found")
    return roles


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db_session),
    _user: User = Depends(require_permissions("admin:manage_roles")),
):
    return db.query(Permission).order_by(Permission.code).all()


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_roles")),
):
    query = db.query(Role).filter(Role.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    roles = query.order_by(Role.name).offset(pagination.offset).limit(pagination.limit).all()
    return [_role_to_out(r) for r in roles]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_roles")),
):
    existing = db.query(Role).filter(Role.tenant_id == user.tenant_id, Role.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A role with this name already exists")

    role = Role(tenant_id=user.tenant_id, name=payload.name)
    role.permissions = _resolve_permissions(db, payload.permission_codes)
    db.add(role)
    db.flush()
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor=user,
        action="role.created",
        entity_type="role",
        entity_id=role.id,
        summary=f"{user.email} created role '{role.name}' with permissions: {', '.join(payload.permission_codes) or 'none'}",
    )
    db.commit()
    db.refresh(role)
    return _role_to_out(role)


def _get_owned_role(db: Session, user: User, role_id: str) -> Role:
    role = db.get(Role, role_id)
    if role is None or role.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: str,
    payload: RoleUpdate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_roles")),
):
    role = _get_owned_role(db, user, role_id)
    if payload.name is not None:
        role.name = payload.name
    if payload.permission_codes is not None:
        role.permissions = _resolve_permissions(db, payload.permission_codes)
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor=user,
        action="role.updated",
        entity_type="role",
        entity_id=role.id,
        summary=f"{user.email} updated role '{role.name}'"
        + (f" — permissions now: {', '.join(payload.permission_codes) or 'none'}" if payload.permission_codes is not None else ""),
    )
    db.commit()
    db.refresh(role)
    return _role_to_out(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: str,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_roles")),
):
    role = _get_owned_role(db, user, role_id)
    if role.is_system:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The system Admin role cannot be deleted")
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor=user,
        action="role.deleted",
        entity_type="role",
        entity_id=role.id,
        summary=f"{user.email} deleted role '{role.name}'",
    )
    db.delete(role)
    db.commit()


@router.get("/users", response_model=list[UserAdminOut])
def list_users(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_users")),
):
    query = db.query(User).filter(User.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    users = query.order_by(User.full_name).offset(pagination.offset).limit(pagination.limit).all()
    return [_user_to_out(u) for u in users]


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_users")),
):
    existing = db.query(User).filter(User.tenant_id == user.tenant_id, User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    new_user = User(
        tenant_id=user.tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_superuser=payload.is_superuser,
    )
    new_user.roles = _resolve_roles(db, user, payload.role_ids)
    db.add(new_user)
    db.flush()
    role_names = ", ".join(r.name for r in new_user.roles) or "none"
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor=user,
        action="user.created",
        entity_type="user",
        entity_id=new_user.id,
        summary=f"{user.email} created user {new_user.email} (roles: {role_names}"
        + (", superuser" if new_user.is_superuser else "")
        + ")",
    )
    db.commit()
    db.refresh(new_user)
    return _user_to_out(new_user)


def _get_owned_target_user(db: Session, user: User, target_id: str) -> User:
    target = db.get(User, target_id)
    if target is None or target.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return target


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:manage_users")),
):
    target = _get_owned_target_user(db, user, user_id)
    if target.id == user.id and payload.is_active is False:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="You cannot deactivate your own account")

    changes: list[str] = []
    if payload.full_name is not None:
        target.full_name = payload.full_name
        changes.append(f"name -> {payload.full_name}")
    if payload.is_active is not None:
        target.is_active = payload.is_active
        changes.append("activated" if payload.is_active else "deactivated")
    if payload.is_superuser is not None:
        target.is_superuser = payload.is_superuser
        changes.append("superuser granted" if payload.is_superuser else "superuser revoked")
    if payload.role_ids is not None:
        target.roles = _resolve_roles(db, user, payload.role_ids)
        changes.append(f"roles -> {', '.join(r.name for r in target.roles) or 'none'}")

    if changes:
        record_audit(
            db,
            tenant_id=user.tenant_id,
            actor=user,
            action="user.updated",
            entity_type="user",
            entity_id=target.id,
            summary=f"{user.email} updated {target.email}: {'; '.join(changes)}",
        )

    db.commit()
    db.refresh(target)
    return _user_to_out(target)


@router.get("/audit-log", response_model=list[AuditLogOut])
def list_audit_log(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
    user: User = Depends(require_permissions("admin:view_audit_log")),
):
    query = db.query(AuditLog).filter(AuditLog.tenant_id == user.tenant_id)
    response.headers["X-Total-Count"] = str(query.count())
    entries = (
        query.options(joinedload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )
    return [_audit_to_out(e) for e in entries]
