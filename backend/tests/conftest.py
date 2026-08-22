import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ATTACHMENTS_DIR", tempfile.mkdtemp(prefix="metam_test_attachments_"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db_session
from app.core.db import Base
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
