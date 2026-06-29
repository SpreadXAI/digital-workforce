"""Team schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import InviteStatus, TeamRole


class TeamOut(BaseModel):
    id: int
    name: str
    is_personal: bool
    role: TeamRole
    member_count: int = 0

    model_config = {"from_attributes": True}


class TeamMemberOut(BaseModel):
    user_id: int
    email: str
    display_name: str
    role: TeamRole
    joined_at: datetime


class TeamInviteCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: TeamRole = TeamRole.member


class TeamInviteOut(BaseModel):
    id: int
    team_id: int
    invitee_email: str
    role: TeamRole
    status: InviteStatus
    token: str
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class TeamInviteAccept(BaseModel):
    token: str
