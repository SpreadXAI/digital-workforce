"""Task center — dispatch work to active employees."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import parse_credentials
from app.models import DigitalEmployee, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import ExecutionOut, TaskCreate, TaskOut
from app.tactile.dispatcher import dispatch_work

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
    emp = (
        db.query(DigitalEmployee)
        .filter(DigitalEmployee.id == body.employee_id, DigitalEmployee.owner_user_id == user.id)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.stage != EmployeeStage.active:
        raise HTTPException(status_code=400, detail="Employee must be active to receive tasks")
    if not emp.tactile_agent_id:
        raise HTTPException(status_code=400, detail="Employee has no Tactile agent — onboard first")

    task = WorkTask(
        employee_id=emp.id,
        title=body.title,
        instruction=body.instruction,
        status=TaskStatus.pending,
        created_by_user_id=user.id,
    )
    db.add(task)
    db.flush()

    try:
        work = await dispatch_work(
            emp.tactile_agent_id,
            body.instruction,
            platform=emp.platform,
            credentials=parse_credentials(emp.credentials),
        )
        work_id = int(work.get("id", 0)) or None
        task.status = TaskStatus.running
        emp.tactile_last_work_id = work_id
        db.add(
            TaskExecution(
                employee_id=emp.id,
                task_id=task.id,
                step="dispatch",
                message=body.instruction,
                status=TaskStatus.running,
                tactile_work_id=work_id,
            )
        )
        db.commit()
        db.refresh(task)
        return task
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
        db.commit()
        logger.exception("Task dispatch failed for employee %s", emp.id)
        raise HTTPException(status_code=502, detail=str(e))


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
