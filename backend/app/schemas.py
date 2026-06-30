"""Pydantic schemas for API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models import EmployeeStage, TaskStatus

EmployeeType = Literal["twitter_operator", "twitter_engagement"]
PlatformType = Literal["twitter"]


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
    employee_type: EmployeeType = "twitter_operator"
    platform: PlatformType = "twitter"
    twitter_handle: str = ""
    twitter_cookie: str = Field(min_length=1, description="Raw cookie or base64-encoded cookie")
    auto_onboard: bool = True


class EmployeeBatchItem(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    employee_type: EmployeeType = "twitter_operator"
    twitter_handle: str = ""
    twitter_cookie: str = Field(min_length=1)


class EmployeeBatchCreate(BaseModel):
    items: list[EmployeeBatchItem] = Field(min_length=1, max_length=200)
    auto_onboard: bool = True


class EmployeeBatchResult(BaseModel):
    created: list["EmployeeOut"]
    failed: list[dict[str, str]]


class TwitterCookieUpdate(BaseModel):
    twitter_cookie: str = Field(min_length=1)


class EmployeeUpdate(BaseModel):
    display_name: str | None = None
    employee_type: EmployeeType | None = None
    twitter_handle: str | None = None
    persona: str | None = None
    playbook: str | None = None
    twitter_cookie: str | None = None


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
    employee_type_label: str = ""
    platform: str
    twitter_handle: str = ""
    persona: str
    playbook: str
    stage: EmployeeStage
    tactile_agent_id: int | None
    tactile_last_work_id: int | None
    has_credentials: bool
    has_twitter_cookie: bool = False
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


class BatchTaskCreate(BaseModel):
    employee_ids: list[int] = Field(min_length=1, max_length=200)
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


class TaskListOut(TaskOut):
    employee_name: str = ""
    employee_handle: str = ""
    tactile_work_id: int | None = None
    tactile_session_id: str | None = None
    tactile_agent_id: int | None = None


class TaskDetailOut(TaskListOut):
    tactile_workspace_id: int | None = None
    tactile_work: dict[str, Any] | None = None
    executions: list["ExecutionOut"] = []


class DispatchInfoOut(BaseModel):
    agent_id: int | None
    workspace_id: int
    api_base: str
    ready: bool


class BatchTaskResult(BaseModel):
    dispatched: list[TaskOut]
    failed: list[dict[str, str]]


class ExecutionOut(BaseModel):
    id: int
    employee_id: int
    task_id: int | None
    step: str
    message: str
    status: TaskStatus
    tactile_work_id: int | None
    tactile_session_id: str | None = None
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
    twitter_active: int = 0


class SkillCatalogItem(BaseModel):
    id: int
    name: str
    slug: str = ""
    description: str = ""
    raw: dict[str, Any] = {}


class TactileSettingsOut(BaseModel):
    api_base: str
    api_key_masked: str
    has_api_key: bool
    workspace_id: int
    agent_id: int | None
    machine_type: str
    configured: bool
    ready: bool


class TactileSettingsUpdate(BaseModel):
    api_base: str | None = None
    api_key: str | None = None
    workspace_id: int | None = None
    agent_id: int | None = None
    machine_type: str | None = None


class TactileHealthOut(BaseModel):
    ok: bool
    status: str = ""
    service: str = ""
    detail: str = ""


EmployeeBatchResult.model_rebuild()
BatchTaskResult.model_rebuild()
TaskDetailOut.model_rebuild()
