from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_schema() -> None:
    if settings.uses_sqlite:
        return
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.database_schema}"'))
        conn.execute(text(f'SET search_path TO "{settings.database_schema}"'))


def init_db() -> None:
    ensure_schema()
    if not settings.uses_sqlite:
        with engine.begin() as conn:
            conn.execute(text(f'SET search_path TO "{settings.database_schema}"'))
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        if not settings.uses_sqlite:
            db.execute(text(f'SET search_path TO "{settings.database_schema}"'))
        yield db
    finally:
        db.close()
