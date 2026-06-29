"""DB schema migrations (lightweight, no Alembic)."""

from sqlalchemy import text

from app.database import engine
from app.config import get_settings

settings = get_settings()
SCHEMA = settings.database_schema


def migrate_schema() -> None:
    """Apply additive schema changes idempotently."""
    if settings.uses_sqlite:
        _migrate_sqlite()
        return
    _migrate_postgres()


def _migrate_sqlite() -> None:
    with engine.begin() as conn:
        tables = {
            row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        if "digital_employees" in tables:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(digital_employees)"))}
            if "twitter_handle" not in cols:
                conn.execute(text("ALTER TABLE digital_employees ADD COLUMN twitter_handle VARCHAR(64) DEFAULT ''"))
            if "team_id" not in cols:
                conn.execute(text("ALTER TABLE digital_employees ADD COLUMN team_id INTEGER"))


def _migrate_postgres() -> None:
    with engine.begin() as conn:
        conn.execute(text(f'SET search_path TO "{SCHEMA}"'))
        conn.execute(
            text(
                f'ALTER TABLE "{SCHEMA}".digital_employees '
                "ADD COLUMN IF NOT EXISTS twitter_handle VARCHAR(64) DEFAULT ''"
            )
        )
        conn.execute(
            text(
                f'ALTER TABLE "{SCHEMA}".digital_employees '
                "ADD COLUMN IF NOT EXISTS team_id INTEGER"
            )
        )
