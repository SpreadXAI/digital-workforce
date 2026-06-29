"""Provision one Tactile Agent per digital employee."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DigitalEmployee, EmployeeStage
from app.tactile.client import tactile

logger = logging.getLogger(__name__)


def build_agent_instructions(employee: DigitalEmployee) -> str:
    parts = [
        f"You are {employee.display_name}, a digital employee in role: {employee.role_title}.",
        f"Platform: {employee.platform or 'general'}.",
    ]
    if employee.persona:
        parts.append(f"\nPersona:\n{employee.persona}")
    if employee.playbook:
        parts.append(f"\nPlaybook:\n{employee.playbook}")
    return "\n".join(parts)


async def provision_agent(db: Session, employee: DigitalEmployee) -> int:
    if not tactile.configured:
        raise RuntimeError("Tactile not configured")

    instructions = build_agent_instructions(employee)
    name = f"dw-{employee.id}-{employee.display_name}"[:120]

    if employee.tactile_agent_id:
        await tactile.update_agent(
            employee.tactile_agent_id,
            name=name,
            instructions=instructions,
        )
        return employee.tactile_agent_id

    agent = await tactile.create_agent(
        name=name,
        instructions=instructions,
        model=settings.tactile_default_model,
    )
    agent_id = int(agent["id"])
    employee.tactile_agent_id = agent_id
    db.commit()
    logger.info("Provisioned Tactile agent %s for employee %s", agent_id, employee.id)
    return agent_id


async def ensure_agent_on_onboard(db: Session, employee: DigitalEmployee) -> int:
    if employee.stage not in (EmployeeStage.ready, EmployeeStage.active):
        raise ValueError("Employee must be ready or active to provision agent")
    return await provision_agent(db, employee)
