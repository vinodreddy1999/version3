from sqlalchemy.orm import Session

from app.core.permissions import PERMISSION_CATALOG
from app.models.user import Permission


def seed_permissions(db: Session) -> None:
    existing_codes = {code for (code,) in db.query(Permission.code).all()}
    for code, description in PERMISSION_CATALOG:
        if code not in existing_codes:
            db.add(Permission(code=code, description=description))
    db.commit()
