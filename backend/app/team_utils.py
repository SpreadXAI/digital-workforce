"""Team helpers — personal team per user, membership checks."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import DigitalEmployee, Team, TeamMember, TeamRole, User


def personal_team_name(user: User) -> str:
    base = user.display_name or user.email.split("@")[0]
    return f"{base} 的团队"


def ensure_personal_team(db: Session, user: User) -> Team:
    membership = (
        db.query(TeamMember)
        .join(Team)
        .filter(TeamMember.user_id == user.id, Team.is_personal.is_(True))
        .first()
    )
    if membership:
        return membership.team

    team = Team(name=personal_team_name(user), is_personal=True, owner_user_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.owner))
    db.flush()
    return team


def list_user_teams(db: Session, user: User) -> list[Team]:
    ensure_personal_team(db, user)
    return (
        db.query(Team)
        .join(TeamMember)
        .filter(TeamMember.user_id == user.id)
        .order_by(Team.is_personal.desc(), Team.id.asc())
        .all()
    )


def get_team_membership(db: Session, user: User, team_id: int) -> TeamMember | None:
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
        .first()
    )


def require_team_member(db: Session, user: User, team_id: int) -> TeamMember:
    m = get_team_membership(db, user, team_id)
    if not m:
        raise HTTPException(status_code=403, detail="Not a member of this team")
    return m


def resolve_team_id(db: Session, user: User, team_id: int | None) -> int:
    if team_id is not None:
        require_team_member(db, user, team_id)
        return team_id
    return ensure_personal_team(db, user).id


def new_invite_token() -> str:
    return secrets.token_urlsafe(32)


def default_invite_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=7)


def get_current_team_id(
    x_team_id: int | None = Header(None, alias="X-Team-Id"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    return resolve_team_id(db, user, x_team_id)


def employee_in_team(db: Session, employee_id: int, team_id: int) -> DigitalEmployee:
    emp = (
        db.query(DigitalEmployee)
        .filter(DigitalEmployee.id == employee_id, DigitalEmployee.team_id == team_id)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp
