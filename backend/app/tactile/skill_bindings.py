"""Sync employee skill bindings to Tactile agent."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import DigitalEmployee, EmployeeSkill
from app.tactile.client import tactile

logger = logging.getLogger(__name__)


async def sync_skills_to_agent(db: Session, employee: DigitalEmployee) -> list[int]:
    if not employee.tactile_agent_id:
        raise RuntimeError("Employee has no Tactile agent")

    bindings = (
        db.query(EmployeeSkill)
        .filter(EmployeeSkill.employee_id == employee.id)
        .all()
    )
    installed: list[int] = []
    for b in bindings:
        try:
            await tactile.install_skill(employee.tactile_agent_id, b.skill_id)
            installed.append(b.skill_id)
        except Exception as e:
            logger.warning("Skill %s install failed for employee %s: %s", b.skill_id, employee.id, e)
    return installed
