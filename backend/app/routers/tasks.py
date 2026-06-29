"""Task center — dispatch work to active employees."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import has_twitter_cookie, parse_credentials
from app.models import DigitalEmployee, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import BatchTaskCreate, BatchTaskResult, ExecutionOut, TaskCreate, TaskOut
from app.tactile.agent_provision import provision_agent
from app.tactile.dispatcher import dispatch_work
from app.tactile.skill_bindings import sync_skills_to_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee_ids = [
        e.id for e in db.query(DigitalEmployee.id).filter(DigitalEmployee.owner_user_id == user.id).all()
    ]
    if not employee_ids:
        return []
    rows = (
        db.query(WorkTask)
        .filter(WorkTask.employee_id.in_(employee_ids))
        .order_by(WorkTask.id.desc())
        .limit(100)
        .all()
    )
    return rows


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task, err = await _dispatch_one(db, user, body.employee_id, body.title, body.instruction)
    if err:
        raise HTTPException(status_code=502, detail=err)
    db.commit()
    db.refresh(task)
    return task


@router.post("/batch", response_model=BatchTaskResult)
async def batch_create_tasks(
    body: BatchTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dispatched: list[TaskOut] = []
    failed: list[dict[str, str]] = []

    for eid in body.employee_ids:
        task, err = await _dispatch_one(db, user, eid, body.title, body.instruction)
        if task:
            dispatched.append(task)
        else:
            emp = db.get(DigitalEmployee, eid)
            failed.append({
                "employee_id": str(eid),
                "display_name": emp.display_name if emp else "",
                "error": err or "unknown",
            })

    db.commit()
    return BatchTaskResult(dispatched=dispatched, failed=failed)


@router.get("/executions", response_model=list[ExecutionOut])
def list_all_executions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee_ids = [
        e.id for e in db.query(DigitalEmployee.id).filter(DigitalEmployee.owner_user_id == user.id).all()
    ]
    if not employee_ids:
        return []
    rows = (
        db.query(TaskExecution)
        .filter(TaskExecution.employee_id.in_(employee_ids))
        .order_by(TaskExecution.id.desc())
        .limit(100)
        .all()
    )
    return rows


async def _dispatch_one(
    db: Session,
    user: User,
    employee_id: int,
    title: str,
    instruction: str,
) -> tuple[TaskOut | None, str | None]:
    emp = (
        db.query(DigitalEmployee)
        .filter(DigitalEmployee.id == employee_id, DigitalEmployee.owner_user_id == user.id)
        .first()
    )
    if not emp:
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

    try:
        if not emp.tactile_agent_id:
            await provision_agent(db, emp)
            await sync_skills_to_agent(db, emp)
            emp.stage = EmployeeStage.active

        work = await dispatch_work(
            emp.tactile_agent_id,
            instruction,
            platform=emp.platform,
            credentials=parse_credentials(emp.credentials),
            employee_id=emp.id,
            twitter_handle=emp.twitter_handle,
        )
        work_id = int(work.get("id", 0)) or None
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
