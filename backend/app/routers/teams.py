"""Team management — personal team, invites, members."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import InviteStatus, Team, TeamInvitation, TeamMember, TeamRole, User
from app.schemas_team import (
    TeamInviteAccept,
    TeamInviteCreate,
    TeamInviteOut,
    TeamMemberOut,
    TeamOut,
)
from app.team_utils import (
    default_invite_expiry,
    ensure_personal_team,
    list_user_teams,
    new_invite_token,
    require_team_member,
    resolve_team_id,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def my_teams(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_personal_team(db, user)
    db.commit()
    teams = list_user_teams(db, user)
    result: list[TeamOut] = []
    for team in teams:
        membership = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
            .first()
        )
        count = db.query(func.count(TeamMember.id)).filter(TeamMember.team_id == team.id).scalar() or 0
        result.append(
            TeamOut(
                id=team.id,
                name=team.name,
                is_personal=team.is_personal,
                role=membership.role if membership else TeamRole.member,
                member_count=count,
            )
        )
    return result


@router.get("/current", response_model=TeamOut)
def current_team(
    x_team_id: int | None = Header(None, alias="X-Team-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team_id = resolve_team_id(db, user, x_team_id)
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    membership = require_team_member(db, user, team_id)
    count = db.query(func.count(TeamMember.id)).filter(TeamMember.team_id == team.id).scalar() or 0
    db.commit()
    return TeamOut(
        id=team.id,
        name=team.name,
        is_personal=team.is_personal,
        role=membership.role,
        member_count=count,
    )


@router.get("/members", response_model=list[TeamMemberOut])
def team_members(
    x_team_id: int | None = Header(None, alias="X-Team-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team_id = resolve_team_id(db, user, x_team_id)
    require_team_member(db, user, team_id)
    rows = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .order_by(TeamMember.role.asc(), TeamMember.joined_at.asc())
        .all()
    )
    return [
        TeamMemberOut(
            user_id=u.id,
            email=u.email,
            display_name=u.display_name,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m, u in rows
    ]


@router.post("/invites", response_model=TeamInviteOut)
def create_invite(
    body: TeamInviteCreate,
    x_team_id: int | None = Header(None, alias="X-Team-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team_id = resolve_team_id(db, user, x_team_id)
    membership = require_team_member(db, user, team_id)
    if membership.role != TeamRole.owner:
        raise HTTPException(status_code=403, detail="Only team owner can invite")

    email = body.email.strip().lower()
    if email == user.email.lower():
        raise HTTPException(status_code=400, detail="Cannot invite yourself")

    invitee = db.query(User).filter(User.email == email).first()
    if invitee:
        existing = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == invitee.id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="User is already a team member")

    pending = (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.team_id == team_id,
            TeamInvitation.invitee_email == email,
            TeamInvitation.status == InviteStatus.pending,
        )
        .first()
    )
    if pending:
        return pending

    inv = TeamInvitation(
        team_id=team_id,
        invitee_email=email,
        token=new_invite_token(),
        role=body.role,
        invited_by_user_id=user.id,
        expires_at=default_invite_expiry(),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/invites", response_model=list[TeamInviteOut])
def list_invites(
    x_team_id: int | None = Header(None, alias="X-Team-Id"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team_id = resolve_team_id(db, user, x_team_id)
    membership = require_team_member(db, user, team_id)
    if membership.role != TeamRole.owner:
        raise HTTPException(status_code=403, detail="Only team owner can list invites")
    rows = (
        db.query(TeamInvitation)
        .filter(TeamInvitation.team_id == team_id, TeamInvitation.status == InviteStatus.pending)
        .order_by(TeamInvitation.id.desc())
        .all()
    )
    return rows


@router.post("/invites/accept", response_model=TeamOut)
def accept_invite(
    body: TeamInviteAccept,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inv = db.query(TeamInvitation).filter(TeamInvitation.token == body.token).first()
    if not inv or inv.status != InviteStatus.pending:
        raise HTTPException(status_code=404, detail="Invite not found or expired")
    if inv.expires_at and inv.expires_at < datetime.now(timezone.utc):
        inv.status = InviteStatus.revoked
        db.commit()
        raise HTTPException(status_code=400, detail="Invite expired")
    if inv.invitee_email.lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="Invite email does not match your account")

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == inv.team_id, TeamMember.user_id == user.id)
        .first()
    )
    if not existing:
        db.add(TeamMember(team_id=inv.team_id, user_id=user.id, role=inv.role))
    inv.status = InviteStatus.accepted
    db.commit()

    team = db.get(Team, inv.team_id)
    membership = require_team_member(db, user, inv.team_id)
    count = db.query(func.count(TeamMember.id)).filter(TeamMember.team_id == team.id).scalar() or 0
    return TeamOut(
        id=team.id,
        name=team.name,
        is_personal=team.is_personal,
        role=membership.role,
        member_count=count,
    )


@router.get("/invites/mine", response_model=list[TeamInviteOut])
def my_pending_invites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(TeamInvitation)
        .filter(
            TeamInvitation.invitee_email == user.email.lower(),
            TeamInvitation.status == InviteStatus.pending,
        )
        .order_by(TeamInvitation.id.desc())
        .all()
    )
