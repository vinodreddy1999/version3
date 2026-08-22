from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.maintenance import router as maintenance_router
from app.api.routes.org import router as org_router
from app.api.routes.procurement import router as procurement_router
from app.api.routes.production import router as production_router
from app.api.routes.quality import router as quality_router
from app.api.routes.reports import router as reports_router
from app.api.routes.sales import router as sales_router
from app.api.routes.warehouse import router as warehouse_router
from app.core.config import settings
from app.core.db import Base, engine
from app.models import *  # noqa: F401,F403  (register all models on Base.metadata)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(org_router)
app.include_router(inventory_router)
app.include_router(warehouse_router)
app.include_router(production_router)
app.include_router(procurement_router)
app.include_router(sales_router)
app.include_router(maintenance_router)
app.include_router(quality_router)
app.include_router(reports_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}
