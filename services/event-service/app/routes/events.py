from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from jose import jwt, JWTError

from app.database import get_db
from app.schemas import EventCreate, EventUpdate, EventResponse
from app.models import EventStatus
from app.services import event_service
from app.config import settings

router = APIRouter()


def get_current_user_info(authorization: Optional[str] = Header(None)) -> Tuple[int, str]:
    """Extract user_id and role from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        ) from exc

    user_id = payload.get("user_id")
    role = payload.get("role", "")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    
    return user_id, role


def require_admin(authorization: Optional[str] = Header(None)) -> None:
    """Ensure request is made by an authenticated admin user."""
    _, role = get_current_user_info(authorization)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )


def require_admin_or_organizer(authorization: Optional[str] = Header(None)) -> Tuple[int, str]:
    """Ensure request is made by an authenticated admin or organizer user."""
    user_id, role = get_current_user_info(authorization)
    if role not in ["admin", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or organizer privileges required"
        )
    return user_id, role


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    user_info: Tuple[int, str] = Depends(require_admin_or_organizer),
):
    """Yeni etkinlik oluştur (Admin veya Organizer)"""
    user_id, role = user_info
    # Organizer ise organizer_id'yi token'dan alınan user_id ile ayarla
    if role == "organizer":
        event.organizer_id = user_id
    return event_service.create_event(db, event)


@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[EventStatus] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Etkinlikleri listele"""
    return event_service.get_events(db, skip=skip, limit=limit, status=status, city=city)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Etkinlik detaylarını getir"""
    event = event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    user_info: Tuple[int, str] = Depends(require_admin_or_organizer),
):
    """Etkinlik bilgilerini güncelle (Admin veya kendi etkinliğinin Organizer'ı)"""
    user_id, role = user_info
    
    # Etkinliği kontrol et
    event = event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Organizer ise sadece kendi etkinliğini düzenleyebilir
    if role == "organizer" and event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own events"
        )
    
    return event_service.update_event(db, event_id, event_update)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user_info: Tuple[int, str] = Depends(require_admin_or_organizer),
):
    """Etkinlik sil (Admin veya kendi etkinliğinin Organizer'ı)"""
    user_id, role = user_info
    
    # Etkinliği kontrol et
    event = event_service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Organizer ise sadece kendi etkinliğini silebilir
    if role == "organizer" and event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own events"
        )
    
    event_service.delete_event(db, event_id)

