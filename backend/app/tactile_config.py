"""Load / persist Tactile Gateway settings (DB overrides env defaults)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PlatformSetting

SETTING_KEYS = (
    "tactile_api_base",
    "tactile_api_key",
    "tactile_workspace_id",
    "tactile_agent_id",
    "tactile_machine_type",
)

ENV_DEFAULTS: dict[str, str] = {
    "tactile_api_base": settings.tactile_api_base,
    "tactile_api_key": settings.tactile_api_key,
    "tactile_workspace_id": str(settings.tactile_workspace_id or ""),
    "tactile_agent_id": str(settings.tactile_template_agent_id or ""),
    "tactile_machine_type": "ubuntu",
}


@dataclass
class TactileRuntimeConfig:
    api_base: str
    api_key: str
    workspace_id: int
    agent_id: int | None
    machine_type: str

    @property
    def base_url(self) -> str:
        return self.api_base.rstrip("/").removesuffix("/api")

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip() and self.workspace_id > 0)

    @property
    def ready(self) -> bool:
        return self.configured and self.agent_id is not None and self.agent_id > 0


def _parse_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_tactile_config(db: Session) -> TactileRuntimeConfig:
    overrides = {row.key: row.value for row in db.query(PlatformSetting).all()}
    merged = {**ENV_DEFAULTS, **overrides}
    workspace_id = _parse_int(merged["tactile_workspace_id"]) or 0
    agent_id = _parse_int(merged["tactile_agent_id"])
    machine_type = (merged.get("tactile_machine_type") or "ubuntu").strip() or "ubuntu"
    return TactileRuntimeConfig(
        api_base=(merged.get("tactile_api_base") or settings.tactile_api_base).strip(),
        api_key=(merged.get("tactile_api_key") or "").strip(),
        workspace_id=workspace_id,
        agent_id=agent_id,
        machine_type=machine_type,
    )


def save_tactile_settings(db: Session, values: dict[str, str | int | None]) -> TactileRuntimeConfig:
    allowed = set(SETTING_KEYS)
    for key, raw in values.items():
        if key not in allowed:
            continue
        text = "" if raw is None else str(raw).strip()
        row = db.get(PlatformSetting, key)
        if not text:
            if row:
                db.delete(row)
            continue
        if row:
            row.value = text
        else:
            db.add(PlatformSetting(key=key, value=text))
    db.flush()
    return load_tactile_config(db)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:4]}...{api_key[-4:]}"


def require_agent_id(config: TactileRuntimeConfig) -> int:
    if not config.configured:
        raise RuntimeError("Tactile 未配置：请在管理台填写 API Key 与工作空间 ID")
    if not config.ready:
        raise RuntimeError("Tactile Agent ID 未配置：请在管理台填写 Agent ID")
    assert config.agent_id is not None
    return config.agent_id
