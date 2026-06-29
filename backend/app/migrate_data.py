"""Backfill teams for existing users and employees."""

from sqlalchemy.orm import Session

from app.models import DigitalEmployee, User
from app.team_utils import ensure_personal_team


def migrate_team_data(db: Session) -> None:
    user_team: dict[int, int] = {}

    for user in db.query(User).all():
        team = ensure_personal_team(db, user)
        user_team[user.id] = team.id

    for emp in db.query(DigitalEmployee).all():
        if not emp.team_id:
            team_id = user_team.get(emp.owner_user_id)
            if team_id:
                emp.team_id = team_id

    db.commit()
