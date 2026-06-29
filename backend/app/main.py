"""Digital Workforce Platform API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.migrate_schema import migrate_schema
from app.models import User  # noqa: F401 — register models
from app.models import User  # noqa: F401 — register models
from app.routers import auth, dashboard, employees, skills, tasks
from app.seed_data import seed_users
from app.tactile.client import tactile

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    migrate_schema()
    db = SessionLocal()
    try:
        if not settings.uses_sqlite:
            db.execute(__import__("sqlalchemy").text(f'SET search_path TO "{settings.database_schema}"'))
        seed_users(db)
    finally:
        db.close()
    yield
    await tactile.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = settings.api_prefix
app.include_router(auth.router, prefix=api)
app.include_router(dashboard.router, prefix=api)
app.include_router(employees.router, prefix=api)
app.include_router(tasks.router, prefix=api)
app.include_router(skills.router, prefix=api)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
