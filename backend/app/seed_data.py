"""Seed default users."""

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.models import User

settings = get_settings()


def seed_users(db: Session) -> None:
    defaults = [
        (settings.admin_email, settings.admin_password, "Admin", True),
        (settings.qa_email, settings.qa_password, "QA", False),
    ]
    for email, password, name, is_admin in defaults:
        if db.query(User).filter(User.email == email).first():
            continue
        db.add(
            User(
                email=email,
                display_name=name,
                password_hash=hash_password(password),
                is_admin=is_admin,
            )
        )
    db.commit()
