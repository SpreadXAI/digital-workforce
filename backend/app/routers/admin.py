"""Admin console — Tactile Gateway settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import User
from app.schemas import TactileHealthOut, TactileSettingsOut, TactileSettingsUpdate
from app.tactile.client import tactile
from app.tactile_config import load_tactile_config, mask_api_key, save_tactile_settings

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_out(config) -> TactileSettingsOut:
    return TactileSettingsOut(
        api_base=config.api_base,
        api_key_masked=mask_api_key(config.api_key),
        has_api_key=bool(config.api_key),
        workspace_id=config.workspace_id,
        agent_id=config.agent_id,
        machine_type=config.machine_type,
        configured=config.configured,
        ready=config.ready,
    )


@router.get("/tactile", response_model=TactileSettingsOut)
def get_tactile_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return _to_out(load_tactile_config(db))


@router.put("/tactile", response_model=TactileSettingsOut)
def update_tactile_settings(
    body: TactileSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    updates: dict[str, str | int | None] = {}
    if body.api_base is not None:
        updates["tactile_api_base"] = body.api_base.strip()
    if body.api_key is not None:
        updates["tactile_api_key"] = body.api_key.strip()
    if body.workspace_id is not None:
        updates["tactile_workspace_id"] = body.workspace_id
    if body.agent_id is not None:
        updates["tactile_agent_id"] = body.agent_id if body.agent_id > 0 else ""
    if body.machine_type is not None:
        updates["tactile_machine_type"] = body.machine_type.strip()

    config = save_tactile_settings(db, updates)
    db.commit()
    return _to_out(config)


@router.post("/tactile/test", response_model=TactileHealthOut)
async def test_tactile_connection(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = load_tactile_config(db)
    if not config.configured:
        raise HTTPException(status_code=400, detail="请先配置 API Key 与工作空间 ID")
    try:
        data = await tactile.health(config)
        return TactileHealthOut(
            ok=True,
            status=str(data.get("status", "ok")),
            service=str(data.get("service", "")),
        )
    except Exception as e:
        return TactileHealthOut(ok=False, detail=str(e))
