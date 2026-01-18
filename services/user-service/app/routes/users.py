from fastapi import APIRouter, Depends, HTTPException, Header, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional, List
from app.config import settings
from app.database import get_db
from app.models import UserRole, User
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter()


def require_admin(authorization: Optional[str] = Header(None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    if payload.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Tüm kullanıcıları listele (Admin only)"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.post(
    "/admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_user(
    admin_data: UserCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Create an admin user (requires existing admin token)."""
    return user_service.create_user(
        db,
        admin_data,
        role=UserRole.ADMIN,
        mark_verified=True,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Kullanıcı bilgilerini getir"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Kullanıcı bilgilerini güncelle"""
    return user_service.update_user(db, user_id, user_update)

