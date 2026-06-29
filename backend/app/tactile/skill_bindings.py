"""Sync employee skill bindings to the shared Tactile Agent."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import DigitalEmployee, EmployeeSkill
from app.tactile.client import tactile
from app.tactile_config import TactileRuntimeConfig, require_agent_id

logger = logging.getLogger(__name__)


async def sync_skills_to_agent(
    db: Session,
    employee: DigitalEmployee,
    config: TactileRuntimeConfig,
) -> list[int]:
    agent_id = require_agent_id(config)
    bindings = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()
    if not bindings:
        return []

    skills = [{"skill_id": b.skill_id, "version_id": b.version_id} for b in bindings]
    try:
        await tactile.update_agent_bindings(config, agent_id, skills=skills)
        return [b.skill_id for b in bindings]
    except Exception as e:
        logger.warning("Skill binding sync failed for employee %s: %s", employee.id, e)
        raise
