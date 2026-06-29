"""Employee helpers."""

from __future__ import annotations

import base64
import binascii
import json
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DigitalEmployee
from app.schemas import EmployeeOut, EmployeeSkillOut

TWITTER_COOKIE_KEY = "TWITTER_COOKIE"

EMPLOYEE_TYPES: dict[str, str] = {
    "twitter_operator": "运营号",
    "twitter_engagement": "互动号",
}

PLATFORM_LABELS: dict[str, str] = {
    "twitter": "Twitter / X",
    "email": "邮箱",
    "other": "其他账号",
}


def next_employee_code(db: Session) -> str:
    count = db.query(func.count(DigitalEmployee.id)).scalar() or 0
    return f"DW-{count + 1:04d}"


def normalize_twitter_cookie_b64(raw: str) -> str:
    """Accept raw cookie string or existing base64; always return base64."""
    value = raw.strip()
    if not value:
        raise ValueError("Twitter Cookie 不能为空")

    try:
        decoded = base64.b64decode(value, validate=True)
        text = decoded.decode("utf-8", errors="ignore")
        if "auth_token" in text or "ct0" in text or "guest_id" in text:
            return value
    except (binascii.Error, ValueError):
        pass

    return base64.b64encode(value.encode()).decode()


def build_twitter_credentials(cookie_raw: str) -> dict[str, str]:
    return {TWITTER_COOKIE_KEY: normalize_twitter_cookie_b64(cookie_raw)}


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


def has_twitter_cookie(emp: DigitalEmployee) -> bool:
    creds = parse_credentials(emp.credentials)
    return bool(creds.get(TWITTER_COOKIE_KEY))


def infer_handle_from_cookie(cookie_raw: str) -> str:
    """Best-effort @handle from cookie value (raw or base64)."""
    try:
        decoded = base64.b64decode(cookie_raw.strip(), validate=True).decode("utf-8", errors="ignore")
    except (binascii.Error, ValueError):
        decoded = cookie_raw
    for key in ("screen_name", "username"):
        m = re.search(rf"{key}=([^;]+)", decoded, re.I)
        if m:
            handle = m.group(1).strip()
            return handle if handle.startswith("@") else f"@{handle}"
    return ""


def employee_to_out(emp: DigitalEmployee) -> EmployeeOut:
    creds = parse_credentials(emp.credentials)
    return EmployeeOut(
        id=emp.id,
        code=emp.code,
        display_name=emp.display_name,
        role_title=emp.role_title,
        employee_type_label=EMPLOYEE_TYPES.get(emp.role_title, emp.role_title),
        platform=emp.platform,
        twitter_handle=emp.twitter_handle or "",
        persona=emp.persona,
        playbook=emp.playbook,
        stage=emp.stage,
        tactile_agent_id=emp.tactile_agent_id,
        tactile_last_work_id=emp.tactile_last_work_id,
        has_credentials=bool(emp.credentials),
        has_twitter_cookie=bool(creds.get(TWITTER_COOKIE_KEY)),
        skills=[EmployeeSkillOut.model_validate(s) for s in emp.skills],
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )
