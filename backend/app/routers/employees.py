"""Digital employee lifecycle: recruit → train → onboard → execute."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.employee_utils import (
    EMPLOYEE_TYPES,
    build_twitter_credentials,
    dump_credentials,
    employee_to_out,
    has_twitter_cookie,
    infer_handle_from_cookie,
    next_employee_code,
    parse_credentials,
)
from app.models import DigitalEmployee, EmployeeSkill, EmployeeStage, TaskExecution, TaskStatus, User, WorkTask
from app.schemas import (
    EmployeeBatchCreate,
    EmployeeBatchResult,
    EmployeeCreate,
    EmployeeOut,
    EmployeeSkillIn,
    EmployeeUpdate,
    ExecutionOut,
    StageTransition,
    TrialRunRequest,
    TwitterCookieUpdate,
)
from app.tactile.agent_provision import ensure_agent_on_onboard, provision_agent
from app.tactile.dispatcher import dispatch_work
from app.tactile.skill_bindings import sync_skills_to_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/types")
def employee_types(_: User = Depends(get_current_user)):
    return {"types": [{"id": k, "label": v} for k, v in EMPLOYEE_TYPES.items()]}


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    stage: EmployeeStage | None = Query(None),
    platform: str | None = Query(None),
    employee_type: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(DigitalEmployee)
    if stage:
        q = q.filter(DigitalEmployee.stage == stage)
    if platform:
        q = q.filter(DigitalEmployee.platform == platform)
    if employee_type:
        q = q.filter(DigitalEmployee.role_title == employee_type)
    rows = q.order_by(DigitalEmployee.id.desc()).all()
    return [employee_to_out(e) for e in rows]


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def recruit_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.employee_type not in EMPLOYEE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported employee type")
    if body.platform != "twitter":
        raise HTTPException(status_code=400, detail="当前仅支持 Twitter 平台")

    handle = body.twitter_handle.strip() or infer_handle_from_cookie(body.twitter_cookie)
    emp = DigitalEmployee(
        code=next_employee_code(db),
        display_name=body.display_name,
        role_title=body.employee_type,
        platform="twitter",
        twitter_handle=handle,
        credentials=dump_credentials(build_twitter_credentials(body.twitter_cookie)),
        stage=EmployeeStage.recruiting,
        owner_user_id=user.id,
    )
    db.add(emp)
    db.flush()
    if body.auto_onboard:
        await _onboard_employee(db, emp)

    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.post("/batch", response_model=EmployeeBatchResult)
async def batch_recruit(
    body: EmployeeBatchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    created: list[EmployeeOut] = []
    failed: list[dict[str, str]] = []

    for idx, item in enumerate(body.items):
        try:
            if item.employee_type not in EMPLOYEE_TYPES:
                raise ValueError(f"不支持的员工类型: {item.employee_type}")
            handle = item.twitter_handle.strip() or infer_handle_from_cookie(item.twitter_cookie)
            emp = DigitalEmployee(
                code=next_employee_code(db),
                display_name=item.display_name,
                role_title=item.employee_type,
                platform="twitter",
                twitter_handle=handle,
                credentials=dump_credentials(build_twitter_credentials(item.twitter_cookie)),
                stage=EmployeeStage.recruiting,
                owner_user_id=user.id,
            )
            db.add(emp)
            db.flush()
            if body.auto_onboard:
                await _onboard_employee(db, emp)
            db.flush()
            created.append(employee_to_out(emp))
        except Exception as e:
            failed.append({"index": str(idx), "display_name": item.display_name, "error": str(e)})

    db.commit()
    return EmployeeBatchResult(created=created, failed=failed)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_employee(db, employee_id)
    return employee_to_out(emp)


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_employee(db, employee_id)
    if body.display_name is not None:
        emp.display_name = body.display_name
    if body.employee_type is not None:
        if body.employee_type not in EMPLOYEE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported employee type")
        emp.role_title = body.employee_type
    if body.twitter_handle is not None:
        emp.twitter_handle = body.twitter_handle
    if body.persona is not None:
        emp.persona = body.persona
    if body.playbook is not None:
        emp.playbook = body.playbook
    if body.twitter_cookie is not None:
        emp.credentials = dump_credentials(build_twitter_credentials(body.twitter_cookie))
        if not emp.twitter_handle:
            emp.twitter_handle = infer_handle_from_cookie(body.twitter_cookie)
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.put("/{employee_id}/cookie", response_model=EmployeeOut)
def update_cookie(
    employee_id: int,
    body: TwitterCookieUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_employee(db, employee_id)
    emp.credentials = dump_credentials(build_twitter_credentials(body.twitter_cookie))
    if not emp.twitter_handle:
        emp.twitter_handle = infer_handle_from_cookie(body.twitter_cookie)
    db.commit()
    db.refresh(emp)
    return employee_to_out(emp)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_employee(db, employee_id)
    db.delete(emp)
    db.commit()


@router.post("/{employee_id}/stage", response_model=EmployeeOut)
async def transition_stage(
    employee_id: int,
    body: StageTransition,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    emp = _get_employee(db, employee_id)
    allowed = _allowed_transitions(emp.stage)
    if body.stage not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition {emp.stage.value} → {body.stage.value}",
        )

    if body.stage == EmployeeStage.active:
        if not has_twitter_cookie(emp):
            raise HTTPException(status_code=400, detail="上岗前须绑定 Twitter Cookie")
        await _onboard_employee(db, emp)
    else:
        emp.stage = body.stage

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
    emp = _get_employee(db, employee_id)
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
    emp = _get_employee(db, employee_id)
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
    emp = _get_employee(db, employee_id)
    if not has_twitter_cookie(emp):
        raise HTTPException(status_code=400, detail="须先绑定 Twitter Cookie")

    try:
        if emp.stage != EmployeeStage.active:
            await _onboard_employee(db, emp)
        elif not emp.tactile_agent_id:
            await provision_agent(db, emp)
            await sync_skills_to_agent(db, emp)

        work = await dispatch_work(
            emp.tactile_agent_id,
            body.instruction,
            platform=emp.platform,
            credentials=parse_credentials(emp.credentials),
            employee_id=emp.id,
            twitter_handle=emp.twitter_handle,
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
    _get_employee(db, employee_id)
    rows = (
        db.query(TaskExecution)
        .filter(TaskExecution.employee_id == employee_id)
        .order_by(TaskExecution.id.desc())
        .limit(50)
        .all()
    )
    return rows


async def _onboard_employee(db: Session, emp: DigitalEmployee) -> None:
    if not has_twitter_cookie(emp):
        raise ValueError("Twitter Cookie 未绑定")
    try:
        await ensure_agent_on_onboard(db, emp)
        await sync_skills_to_agent(db, emp)
        emp.stage = EmployeeStage.active
    except Exception as e:
        logger.exception("Onboard failed for employee %s", emp.id)
        raise


def _get_employee(db: Session, employee_id: int) -> DigitalEmployee:
    emp = db.query(DigitalEmployee).filter(DigitalEmployee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


def _allowed_transitions(current: EmployeeStage) -> set[EmployeeStage]:
    graph: dict[EmployeeStage, set[EmployeeStage]] = {
        EmployeeStage.recruiting: {EmployeeStage.training, EmployeeStage.active},
        EmployeeStage.training: {EmployeeStage.ready, EmployeeStage.active, EmployeeStage.recruiting},
        EmployeeStage.ready: {EmployeeStage.active, EmployeeStage.training},
        EmployeeStage.active: {EmployeeStage.suspended, EmployeeStage.training},
        EmployeeStage.suspended: {EmployeeStage.active, EmployeeStage.training},
    }
    return graph.get(current, set())
