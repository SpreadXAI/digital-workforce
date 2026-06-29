import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmployeeStage(str, enum.Enum):
    recruiting = "recruiting"
    training = "training"
    ready = "ready"
    active = "active"
    suspended = "suspended"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class TeamRole(str, enum.Enum):
    owner = "owner"
    member = "member"


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    revoked = "revoked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["TeamMember"]] = relationship(back_populates="user")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    invitations: Mapped[list["TeamInvitation"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    employees: Mapped[list["DigitalEmployee"]] = relationship(back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.member)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    invitee_email: Mapped[str] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[TeamRole] = mapped_column(Enum(TeamRole), default=TeamRole.member)
    status: Mapped[InviteStatus] = mapped_column(Enum(InviteStatus), default=InviteStatus.pending)
    invited_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[Team] = relationship(back_populates="invitations")


class DigitalEmployee(Base):
    __tablename__ = "digital_employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    role_title: Mapped[str] = mapped_column(String(64), default="twitter_operator")
    platform: Mapped[str] = mapped_column(String(32), default="twitter")
    twitter_handle: Mapped[str] = mapped_column(String(64), default="")
    persona: Mapped[str] = mapped_column(Text, default="")
    playbook: Mapped[str] = mapped_column(Text, default="")
    credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage: Mapped[EmployeeStage] = mapped_column(Enum(EmployeeStage), default=EmployeeStage.recruiting)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True, nullable=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    tactile_agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tactile_last_work_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    skills: Mapped[list["EmployeeSkill"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    tasks: Mapped[list["WorkTask"]] = relationship(back_populates="employee")
    executions: Mapped[list["TaskExecution"]] = relationship(back_populates="employee")
    team: Mapped[Team] = relationship(back_populates="employees")


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("digital_employees.id"), index=True)
    skill_id: Mapped[int] = mapped_column(Integer)
    version_id: Mapped[int] = mapped_column(Integer)
    slug: Mapped[str] = mapped_column(String(128), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    inputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    outputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[DigitalEmployee] = relationship(back_populates="skills")


class WorkTask(Base):
    __tablename__ = "work_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("digital_employees.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    instruction: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.pending)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[DigitalEmployee] = relationship(back_populates="tasks")
    executions: Mapped[list["TaskExecution"]] = relationship(back_populates="task")


class TaskExecution(Base):
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("digital_employees.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("work_tasks.id"), nullable=True)
    step: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.completed)
    tactile_work_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tactile_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    employee: Mapped[DigitalEmployee] = relationship(back_populates="executions")
    task: Mapped[WorkTask | None] = relationship(back_populates="executions")
