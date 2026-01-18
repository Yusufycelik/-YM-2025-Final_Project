import os
import sys
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.database import SessionLocal  # noqa: E402
from app.models import UserRole  # noqa: E402
from app.schemas import UserCreate  # noqa: E402
from app.services import user_service  # noqa: E402


def create_admin(
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
) -> None:
    """
    Create a default admin user if it does not exist.

    Usage (inside the user-service container):

        python scripts/create_admin.py
    """
    db = SessionLocal()
    try:
        existing = user_service.get_user_by_email(db, email)
        if existing:
            print(
                "[create_admin] User with email '%s' already exists (role=%s). Skipping."
                % (email, existing.role.value)
            )
            return

        payload = UserCreate(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            phone=phone,
        )

        admin_user = user_service.create_user(
            db,
            payload,
            role=UserRole.ADMIN,
            mark_verified=True,
        )
        print(
            "[create_admin] Admin user created with email '%s' and id %s."
            % (admin_user.email, admin_user.id)
        )
    finally:
        db.close()


if __name__ == "__main__":
    default_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    default_username = os.getenv("ADMIN_USERNAME", "admin")
    default_password = os.getenv("ADMIN_PASSWORD", "admin123")
    default_full_name = os.getenv("ADMIN_FULL_NAME", "Administrator")
    default_phone = os.getenv("ADMIN_PHONE")

    create_admin(
        email=default_email,
        username=default_username,
        password=default_password,
        full_name=default_full_name,
        phone=default_phone,
    )


