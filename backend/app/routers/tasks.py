"""Task center — dispatch work via shared Tactile Agent."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import has_twitter_cookie, parse_credentials
from app.models import DigitalEmployee, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import BatchTaskCreate, BatchTaskResult, ExecutionOut, TaskCreate, TaskOut
from app.team_utils import employee_in_team, get_current_team_id
from app.tactile.dispatcher import dispatch_work
from app.tactile_config import load_tactile_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


def _team_employee_ids(db: Session, team_id: int) -> list[int]:
    return [e.id for e in db.query(DigitalEmployee.id).filter(DigitalEmployee.team_id == team_id).all()]


@router.get("", response_model=list[TaskOut])
def list_tasks(
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    employee_ids = _team_employee_ids(db, team_id)
    if not employee_ids:
        return []
    return (
        db.query(WorkTask)
        .filter(WorkTask.employee_id.in_(employee_ids))
        .order_by(WorkTask.id.desc())
        .limit(100)
        .all()
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
