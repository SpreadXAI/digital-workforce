"""Pydantic schemas for API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import EmployeeStage, TaskStatus


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    is_admin: bool

    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    role_title: str = "twitter_operator"
    platform: str = "twitter"


class EmployeeUpdate(BaseModel):
    display_name: str | None = None
    role_title: str | None = None
    platform: str | None = None
    persona: str | None = None
    playbook: str | None = None
    credentials: dict[str, str] | None = None


class EmployeeSkillIn(BaseModel):
    skill_id: int
    version_id: int
    slug: str = ""
    name: str = ""
    inputs_json: str | None = None
    outputs_json: str | None = None


class EmployeeSkillOut(BaseModel):
    id: int
    skill_id: int
    version_id: int
    slug: str
    name: str

    model_config = {"from_attributes": True}


class EmployeeOut(BaseModel):
    id: int
    code: str
    display_name: str
    role_title: str
    platform: str
    persona: str
    playbook: str
    stage: EmployeeStage
    tactile_agent_id: int | None
    tactile_last_work_id: int | None
    has_credentials: bool
    skills: list[EmployeeSkillOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StageTransition(BaseModel):
    stage: EmployeeStage


class TrialRunRequest(BaseModel):
    instruction: str = Field(min_length=1)


class TaskCreate(BaseModel):
    employee_id: int
    title: str = Field(min_length=1, max_length=200)
    instruction: str = Field(min_length=1)


class TaskOut(BaseModel):
    id: int
    employee_id: int
    title: str
    instruction: str
    status: TaskStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionOut(BaseModel):
    id: int
    employee_id: int
    task_id: int | None
    step: str
    message: str
    status: TaskStatus
    tactile_work_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_employees: int
    recruiting: int
    training: int
    ready: int
    active: int
    suspended: int
    tasks_today: int


class SkillCatalogItem(BaseModel):
    id: int
    name: str
    slug: str = ""
    description: str = ""
    raw: dict[str, Any] = {}
