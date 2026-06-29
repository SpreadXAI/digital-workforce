"""Digital employee lifecycle: recruit → train → onboard → execute."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import dump_credentials, employee_to_out, next_employee_code, parse_credentials
from app.models import DigitalEmployee, EmployeeSkill, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeSkillIn,
    EmployeeUpdate,
    ExecutionOut,
    StageTransition,
    TrialRunRequest,
)
from app.tactile.agent_provision import ensure_agent_on_onboard, provision_agent
from app.tactile.dispatcher import dispatch_work
from app.tactile.skill_bindings import sync_skills_to_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    stage: EmployeeStage | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(DigitalEmployee).filter(DigitalEmployee.owner_user_id == user.id)
    if stage:
        q = q.filter(DigitalEmployee.stage == stage)
    rows = q.order_by(DigitalEmployee.id.desc()).all()
    return [employee_to_out(e) for e in rows]


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def recruit_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = DigitalEmployee(
        code=next_employee_code(db),
        display_name=body.display_name,
        role_title=body.role_title,
        platform=body.platform,
        stage=EmployeeStage.recruiting,
        owner_user_id=user.id,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    return employee_to_out(emp)


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    if body.display_name is not None:
        emp.display_name = body.display_name
    if body.role_title is not None:
        emp.role_title = body.role_title
    if body.platform is not None:
        emp.platform = body.platform
    if body.persona is not None:
        emp.persona = body.persona
    if body.playbook is not None:
        emp.playbook = body.playbook
    if body.credentials is not None:
        emp.credentials = dump_credentials(body.credentials)
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.post("/{employee_id}/stage", response_model=EmployeeOut)
async def transition_stage(
    employee_id: int,
    body: StageTransition,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    allowed = _allowed_transitions(emp.stage)
    if body.stage not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition {emp.stage.value} → {body.stage.value}",
        )
    emp.stage = body.stage

    if body.stage == EmployeeStage.active:
        try:
            await ensure_agent_on_onboard(db, emp)
            await sync_skills_to_agent(db, emp)
        except Exception as e:
            logger.exception("Onboard failed for employee %s", employee_id)
            raise HTTPException(status_code=502, detail=f"Tactile onboard failed: {e}")

    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.post("/{employee_id}/skills", response_model=EmployeeOut)
def bind_skill(
    employee_id: int,
    body: EmployeeSkillIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    if emp.stage not in (EmployeeStage.training, EmployeeStage.ready, EmployeeStage.active):
        raise HTTPException(status_code=400, detail="Skills can only be bound during training or later")

    existing = (
        db.query(EmployeeSkill)
        .filter(EmployeeSkill.employee_id == emp.id, EmployeeSkill.skill_id == body.skill_id)
        .first()
    )
    if existing:
        existing.version_id = body.version_id
        existing.slug = body.slug
        existing.name = body.name
        existing.inputs_json = body.inputs_json
        existing.outputs_json = body.outputs_json
    else:
        db.add(
            EmployeeSkill(
                employee_id=emp.id,
                skill_id=body.skill_id,
                version_id=body.version_id,
                slug=body.slug,
                name=body.name,
                inputs_json=body.inputs_json,
                outputs_json=body.outputs_json,
            )
        )
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.delete("/{employee_id}/skills/{skill_id}", response_model=EmployeeOut)
def unbind_skill(
    employee_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    db.query(EmployeeSkill).filter(
        EmployeeSkill.employee_id == emp.id,
        EmployeeSkill.skill_id == skill_id,
    ).delete()
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.post("/{employee_id}/trial-run", response_model=ExecutionOut)
async def trial_run(
    employee_id: int,
    body: TrialRunRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_owned(db, user, employee_id)
    if emp.stage not in (EmployeeStage.training, EmployeeStage.ready, EmployeeStage.active):
        raise HTTPException(status_code=400, detail="Trial run only in training/ready/active")

    try:
        if not emp.tactile_agent_id:
            await provision_agent(db, emp)
            await sync_skills_to_agent(db, emp)

        work = await dispatch_work(
            emp.tactile_agent_id,
            body.instruction,
            platform=emp.platform,
            credentials=parse_credentials(emp.credentials),
        )
        work_id = int(work.get("id", 0)) or None
        emp.tactile_last_work_id = work_id
        execution = TaskExecution(
            employee_id=emp.id,
            step="trial_run",
            message=body.instruction,
            status=TaskStatus.running,
            tactile_work_id=work_id,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution
    except Exception as e:
        logger.exception("Trial run failed for employee %s", employee_id)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{employee_id}/executions", response_model=list[ExecutionOut])
def list_executions(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned(db, user, employee_id)
    rows = (
        db.query(TaskExecution)
        .filter(TaskExecution.employee_id == employee_id)
        .order_by(TaskExecution.id.desc())
        .limit(50)
        .all()
    )
    return rows


def _get_owned(db: Session, user: User, employee_id: int) -> DigitalEmployee:
    emp = (
        db.query(DigitalEmployee)
        .filter(DigitalEmployee.id == employee_id, DigitalEmployee.owner_user_id == user.id)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


def _allowed_transitions(current: EmployeeStage) -> set[EmployeeStage]:
    graph: dict[EmployeeStage, set[EmployeeStage]] = {
        EmployeeStage.recruiting: {EmployeeStage.training},
        EmployeeStage.training: {EmployeeStage.ready, EmployeeStage.recruiting},
        EmployeeStage.ready: {EmployeeStage.active, EmployeeStage.training},
        EmployeeStage.active: {EmployeeStage.suspended, EmployeeStage.training},
        EmployeeStage.suspended: {EmployeeStage.active, EmployeeStage.training},
    }
    return graph.get(current, set())
