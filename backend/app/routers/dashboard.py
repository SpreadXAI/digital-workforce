"""Dashboard stats."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import DigitalEmployee, EmployeeStage, User, WorkTask
from app.schemas import DashboardStats
from app.team_utils import get_current_team_id

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(
    team_id: int = Depends(get_current_team_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    total = db.query(func.count(DigitalEmployee.id)).filter(DigitalEmployee.team_id == team_id).scalar() or 0
    by_stage = {
        row[0]: row[1]
        for row in db.query(DigitalEmployee.stage, func.count(DigitalEmployee.id))
        .filter(DigitalEmployee.team_id == team_id)
        .group_by(DigitalEmployee.stage)
    }
    employee_ids = [e.id for e in db.query(DigitalEmployee.id).filter(DigitalEmployee.team_id == team_id).all()]
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tasks_today = 0
    if employee_ids:
        tasks_today = (
            db.query(func.count(WorkTask.id))
            .filter(WorkTask.employee_id.in_(employee_ids), WorkTask.created_at >= today_start)
            .scalar()
            or 0
        )
    twitter_active = (
        db.query(func.count(DigitalEmployee.id))
        .filter(
            DigitalEmployee.team_id == team_id,
            DigitalEmployee.platform == "twitter",
            DigitalEmployee.stage == EmployeeStage.active,
        )
        .scalar()
        or 0
    )
    return DashboardStats(
        total_employees=total,
        recruiting=by_stage.get(EmployeeStage.recruiting, 0),
        training=by_stage.get(EmployeeStage.training, 0),
        ready=by_stage.get(EmployeeStage.ready, 0),
        active=by_stage.get(EmployeeStage.active, 0),
        suspended=by_stage.get(EmployeeStage.suspended, 0),
        tasks_today=tasks_today,
        twitter_active=twitter_active,
    )
