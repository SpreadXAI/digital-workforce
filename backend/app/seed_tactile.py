"""Seed platform settings from environment on startup."""

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PlatformSetting


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
