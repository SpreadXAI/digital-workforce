"""Skill catalog proxy (Tactile Skill Plaza)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import User
from app.schemas import SkillCatalogItem
from app.tactile.client import tactile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/catalog", response_model=list[SkillCatalogItem])
async def skill_catalog(_: User = Depends(get_current_user)):
    if not tactile.configured:
        return []
    try:
        items = await tactile.list_skill_plaza()
        result: list[SkillCatalogItem] = []
        for item in items:
            result.append(
                SkillCatalogItem(
                    id=int(item.get("id", 0)),
                    name=str(item.get("name", "")),
                    slug=str(item.get("slug", "")),
                    description=str(item.get("description", "")),
                    raw=item,
                )
            )
        return result
    except Exception as e:
        logger.exception("Skill catalog fetch failed")
        raise HTTPException(status_code=502, detail=str(e))
