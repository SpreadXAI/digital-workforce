"""Seed / sync platform Tactile (Cloud Agent Lab) settings from environment."""

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PlatformSetting
from app.tactile_config import save_tactile_settings


def _ensure(db: Session, key: str, value: str | int | None) -> None:
    if value is None or value == "" or value == 0:
        return
    if db.get(PlatformSetting, key):
        return
    db.add(PlatformSetting(key=key, value=str(value)))


def seed_tactile_settings(db: Session) -> None:
    """Insert env defaults only when DB has no admin override for that key."""
    _ensure(db, "tactile_api_base", settings.tactile_api_base)
    _ensure(db, "tactile_api_key", settings.tactile_api_key)
    _ensure(db, "tactile_workspace_id", settings.tactile_workspace_id)
    _ensure(db, "tactile_agent_id", settings.tactile_template_agent_id)
    db.commit()


def sync_tactile_settings_from_env(db: Session) -> None:
    """Production: align platform_settings with backend/.env on each startup/deploy."""
    if settings.environment != "production":
        return
    if not settings.uses_sqlite:
        from sqlalchemy import text

        db.execute(text(f'SET search_path TO "{settings.database_schema}"'))
    save_tactile_settings(
        db,
        {
            "tactile_api_base": settings.tactile_api_base,
            "tactile_api_key": settings.tactile_api_key,
            "tactile_workspace_id": settings.tactile_workspace_id,
            "tactile_agent_id": settings.tactile_template_agent_id,
            "tactile_machine_type": "ubuntu",
        },
    )
    db.commit()
