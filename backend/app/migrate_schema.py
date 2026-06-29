"""DB schema migrations (lightweight, no Alembic)."""

from sqlalchemy import text

from app.database import engine
from app.config import get_settings

settings = get_settings()


def migrate_schema() -> None:
    """Apply additive schema changes idempotently."""
    if settings.uses_sqlite:
        with engine.begin() as conn:
            tables = {
                row[0]
                for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            }
            if "digital_employees" not in tables:
                return
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(digital_employees)"))}
            if "twitter_handle" not in cols:
                conn.execute(text("ALTER TABLE digital_employees ADD COLUMN twitter_handle VARCHAR(64) DEFAULT ''"))
        return

    with engine.begin() as conn:
        conn.execute(text(f'SET search_path TO "{settings.database_schema}"'))
        conn.execute(
            text(
                f'ALTER TABLE "{settings.database_schema}".digital_employees '
                "ADD COLUMN IF NOT EXISTS twitter_handle VARCHAR(64) DEFAULT ''"
            )
        )
