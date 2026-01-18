from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from jose import jwt, JWTError
from app.database import get_db
from app.schemas import TicketCreate, TicketResponse, TicketUpdate, AdminTicketCreate
from app.services import ticket_service
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


def require_user_role(authorization: Optional[str] = Header(None)) -> Tuple[int, str]:
    """Ensure request is made by a user (not admin or organizer)."""
    user_id, role = get_current_user_info(authorization)
    if role in ["admin", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin and organizer users cannot purchase tickets"
        )
    return user_id, role


def require_admin(authorization: Optional[str] = Header(None)) -> Tuple[int, str]:
    """Ensure request is made by an authenticated admin user."""
    user_id, role = get_current_user_info(authorization)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user_id, role


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    user_info: Tuple[int, str] = Depends(require_user_role)
):
    """Bilet rezervasyonu oluştur (Sadece user rolü)"""
    current_user_id, _ = user_info
    # Kullanıcı sadece kendi adına bilet alabilir
    if ticket.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only purchase tickets for yourself"
        )
    return await ticket_service.create_ticket(db, ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Bilet bilgilerini getir"""
    ticket = ticket_service.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.get("/number/{ticket_number}", response_model=TicketResponse)
async def get_ticket_by_number(ticket_number: str, db: Session = Depends(get_db)):
    """Bilet numarası ile bilet bilgilerini getir"""
    ticket = ticket_service.get_ticket_by_number(db, ticket_number)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.get("/user/{user_id}", response_model=List[TicketResponse])
async def get_user_tickets(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Kullanıcının biletlerini listele"""
    return ticket_service.get_user_tickets(db, user_id, skip=skip, limit=limit)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """Bilet bilgilerini güncelle"""
    return ticket_service.update_ticket(db, ticket_id, ticket_update)


@router.post("/{ticket_id}/cancel", response_model=TicketResponse)
async def cancel_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Bilet iptali"""
    return ticket_service.cancel_ticket(db, ticket_id)


@router.post("/admin/assign", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def admin_assign_ticket(
    ticket: AdminTicketCreate,
    db: Session = Depends(get_db),
    admin_info: Tuple[int, str] = Depends(require_admin)
):
    """Admin tarafından kullanıcıya bilet atama (Sadece user rolü için)"""
    # Kullanıcının rolünü kontrol et (user-service'den)
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                f"{settings.USER_SERVICE_URL}/api/v1/users/{ticket.user_id}",
                timeout=5.0
            )
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            user_data = user_response.json()
            if user_data.get("role") != "user":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tickets can only be assigned to users with 'user' role"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )
    
    # Bilet oluştur
    ticket_create = TicketCreate(
        event_id=ticket.event_id,
        user_id=ticket.user_id,
        quantity=ticket.quantity
    )
    return await ticket_service.create_ticket(db, ticket_create)


@router.delete("/admin/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    admin_info: Tuple[int, str] = Depends(require_admin)
):
    """Admin tarafından bilet silme"""
    from app.models import Ticket
    db_ticket = ticket_service.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Bilet iptal et (stok geri verir)
    ticket_service.cancel_ticket(db, ticket_id)
    
    # Bileti veritabanından sil
    db.delete(db_ticket)
    db.commit()
    
    return None

