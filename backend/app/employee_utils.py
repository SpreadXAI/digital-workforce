"""Employee helpers."""

from __future__ import annotations

import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DigitalEmployee
from app.schemas import EmployeeOut, EmployeeSkillOut


def next_employee_code(db: Session) -> str:
    count = db.query(func.count(DigitalEmployee.id)).scalar() or 0
    return f"DW-{count + 1:04d}"


def parse_credentials(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return {str(k): str(v) for k, v in data.items() if v}
    except json.JSONDecodeError:
        return {}


def dump_credentials(data: dict[str, str] | None) -> str | None:
    if not data:
        return None
    cleaned = {k: v for k, v in data.items() if v}
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def employee_to_out(emp: DigitalEmployee) -> EmployeeOut:
    return EmployeeOut(
        id=emp.id,
        code=emp.code,
        display_name=emp.display_name,
        role_title=emp.role_title,
        platform=emp.platform,
        persona=emp.persona,
        playbook=emp.playbook,
        stage=emp.stage,
        tactile_agent_id=emp.tactile_agent_id,
        tactile_last_work_id=emp.tactile_last_work_id,
        has_credentials=bool(emp.credentials),
        skills=[EmployeeSkillOut.model_validate(s) for s in emp.skills],
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )
