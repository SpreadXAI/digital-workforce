"""Task center — dispatch work via shared Tactile Agent."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import has_twitter_cookie, parse_credentials
from app.models import DigitalEmployee, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import BatchTaskCreate, BatchTaskResult, DispatchInfoOut, ExecutionOut, TaskCreate, TaskDetailOut, TaskListOut, TaskOut
from app.team_utils import employee_in_team, get_current_team_id
from app.tactile.client import tactile
from app.tactile.dispatcher import dispatch_work
from app.tactile_config import load_tactile_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

_TACTILE_STATUS_MAP: dict[str, TaskStatus] = {
    "idle": TaskStatus.running,
    "running": TaskStatus.running,
    "coding": TaskStatus.running,
    "completed": TaskStatus.completed,
    "archived": TaskStatus.completed,
    "failed": TaskStatus.failed,
}


def _team_employee_ids(db: Session, team_id: int) -> list[int]:
    return [e.id for e in db.query(DigitalEmployee.id).filter(DigitalEmployee.team_id == team_id).all()]


def _latest_execution(db: Session, task_id: int) -> TaskExecution | None:
    return (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id)
        .order_by(TaskExecution.id.desc())
        .first()
    )


def _task_list_out(db: Session, task: WorkTask, config_agent_id: int | None) -> TaskListOut:
    emp = db.get(DigitalEmployee, task.employee_id)
    ex = _latest_execution(db, task.id)
    return TaskListOut(
        id=task.id,
        employee_id=task.employee_id,
        title=task.title,
        instruction=task.instruction,
        status=task.status,
        created_at=task.created_at,
        employee_name=emp.display_name if emp else "",
        employee_handle=emp.twitter_handle if emp else "",
        tactile_work_id=ex.tactile_work_id if ex else None,
        tactile_session_id=ex.tactile_session_id if ex else None,
        tactile_agent_id=config_agent_id,
    )


def _sync_task_from_tactile(task: WorkTask, tactile_work: dict[str, Any] | None) -> None:
    if not tactile_work:
        return
    mapped = _TACTILE_STATUS_MAP.get(str(tactile_work.get("status", "")).lower())
    if mapped:
        task.status = mapped


@router.get("", response_model=list[TaskListOut])
def list_tasks(
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    config = load_tactile_config(db)
    employee_ids = _team_employee_ids(db, team_id)
    if not employee_ids:
        return []
    rows = (
        db.query(WorkTask)
        .filter(WorkTask.employee_id.in_(employee_ids))
        .order_by(WorkTask.id.desc())
        .limit(100)
        .all()
    )
    return [_task_list_out(db, t, config.agent_id) for t in rows]


@router.get("/dispatch-info", response_model=DispatchInfoOut)
def dispatch_info(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    config = load_tactile_config(db)
    return DispatchInfoOut(
        agent_id=config.agent_id,
        workspace_id=config.workspace_id,
        api_base=config.api_base,
        ready=config.ready,
    )


@router.get("/executions", response_model=list[ExecutionOut])
def list_all_executions(
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    employee_ids = _team_employee_ids(db, team_id)
    if not employee_ids:
        return []
    return (
        db.query(TaskExecution)
        .filter(TaskExecution.employee_id.in_(employee_ids))
        .order_by(TaskExecution.id.desc())
        .limit(100)
        .all()
    )


@router.get("/{task_id}", response_model=TaskDetailOut)
async def get_task(
    task_id: int,
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    task = db.get(WorkTask, task_id)
    if not task or task.employee_id not in _team_employee_ids(db, team_id):
        raise HTTPException(status_code=404, detail="Task not found")

    config = load_tactile_config(db)
    base = _task_list_out(db, task, config.agent_id)
    executions = (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task.id)
        .order_by(TaskExecution.id.asc())
        .all()
    )
    tactile_work: dict[str, Any] | None = None
    work_id = base.tactile_work_id
    if work_id and config.configured:
        try:
            tactile_work = await tactile.get_work(config, work_id)
            _sync_task_from_tactile(task, tactile_work)
            db.commit()
            db.refresh(task)
            base.status = task.status
        except Exception as e:
            logger.warning("Failed to fetch tactile work %s: %s", work_id, e)

    return TaskDetailOut(
        **base.model_dump(),
        tactile_workspace_id=config.workspace_id,
        tactile_work=tactile_work,
        executions=[ExecutionOut.model_validate(e) for e in executions],
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task, err = await _dispatch_one(db, user, team_id, body.employee_id, body.title, body.instruction)
    if err:
        raise HTTPException(status_code=502, detail=err)
    db.commit()
    db.refresh(task)
    return task


@router.post("/batch", response_model=BatchTaskResult)
async def batch_create_tasks(
    body: BatchTaskCreate,
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dispatched: list[TaskOut] = []
    failed: list[dict[str, str]] = []

    for eid in body.employee_ids:
        task, err = await _dispatch_one(db, user, team_id, eid, body.title, body.instruction)
        if task:
            dispatched.append(task)
        else:
            try:
                emp = employee_in_team(db, eid, team_id)
                name = emp.display_name
            except HTTPException:
                name = ""
            failed.append({"employee_id": str(eid), "display_name": name, "error": err or "unknown"})

    db.commit()
    return BatchTaskResult(dispatched=dispatched, failed=failed)


async def _dispatch_one(
    db: Session,
    user: User,
    team_id: int,
    employee_id: int,
    title: str,
    instruction: str,
) -> tuple[TaskOut | None, str | None]:
    try:
        emp = employee_in_team(db, employee_id, team_id)
    except HTTPException:
        return None, "员工不存在"
    if not has_twitter_cookie(emp):
        return None, "未绑定 Twitter Cookie"
    if emp.stage not in (
        EmployeeStage.active,
        EmployeeStage.ready,
        EmployeeStage.training,
        EmployeeStage.recruiting,
    ):
        return None, f"员工状态 {emp.stage.value} 不可派活"

    task = WorkTask(
        employee_id=emp.id,
        title=title,
        instruction=instruction,
        status=TaskStatus.pending,
        created_by_user_id=user.id,
    )
    db.add(task)
    db.flush()

    config = load_tactile_config(db)

    try:
        work = await dispatch_work(
            config,
            title=title,
            content=instruction,
            platform=emp.platform,
            credentials=parse_credentials(emp.credentials),
            employee_id=emp.id,
            twitter_handle=emp.twitter_handle,
        )
        work_id = int(work.get("id", 0)) or None
        session_id = work.get("session_id")
        task.status = TaskStatus.running
        emp.tactile_last_work_id = work_id
        emp.stage = EmployeeStage.active
        db.add(
            TaskExecution(
                employee_id=emp.id,
                task_id=task.id,
                step="dispatch",
                message=instruction,
                status=TaskStatus.running,
                tactile_work_id=work_id,
                tactile_session_id=str(session_id) if session_id else None,
            )
        )
        db.flush()
        return task, None
    except Exception as e:
        task.status = TaskStatus.failed
        db.add(
            TaskExecution(
                employee_id=emp.id,
                task_id=task.id,
                step="dispatch",
                message=str(e),
                status=TaskStatus.failed,
            )
        )
        db.flush()
        logger.exception("Task dispatch failed for employee %s", emp.id)
        return None, str(e)
