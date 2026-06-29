"""Seed default users and personal teams."""

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.models import User
from app.team_utils import ensure_personal_team

settings = get_settings()


def seed_users(db: Session) -> None:
    defaults = [
        (settings.admin_email, settings.admin_password, "Admin", True),
        (settings.qa_email, settings.qa_password, "QA", False),
    ]
    for email, password, name, is_admin in defaults:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                display_name=name,
                password_hash=hash_password(password),
                is_admin=is_admin,
            )
            db.add(user)
            db.flush()
        ensure_personal_team(db, user)
    db.commit()
