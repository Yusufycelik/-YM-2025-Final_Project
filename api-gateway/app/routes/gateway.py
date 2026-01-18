from fastapi import APIRouter, Request, HTTPException, status, Depends, Header
from fastapi.responses import Response
from typing import Optional
from app.config import settings
from app.utils.proxy import proxy_request
from app.utils.auth import get_current_user

router = APIRouter()


def get_authorization_header(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Authorization header'ı al"""
    return authorization


# User Service Routes
@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    """User service authentication endpoints"""
    return await proxy_request(
        settings.USER_SERVICE_URL,
        f"/api/v1/auth/{path}",
        request.method,
        request
    )


@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def users_proxy(
    path: str,
    request: Request,
    authorization: Optional[str] = Depends(get_authorization_header)
):
    """User service endpoints (requires authentication)"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Token doğrula
    token = authorization.replace("Bearer ", "")
    get_current_user(token)
    
    return await proxy_request(
        settings.USER_SERVICE_URL,
        f"/api/v1/users/{path}",
        request.method,
        request
    )


# Event Service Routes
@router.api_route("/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def events_proxy(
    path: str,
    request: Request,
    authorization: Optional[str] = Depends(get_authorization_header)
):
    """Event service endpoints"""
    headers = {}
    if authorization:
        token = authorization.replace("Bearer ", "")
        get_current_user(token)  # Token doğrula
        headers["Authorization"] = authorization
    
    return await proxy_request(
        settings.EVENT_SERVICE_URL,
        f"/api/v1/events/{path}",
        request.method,
        request,
        headers
    )


# Ticket Service Routes
@router.api_route("/tickets/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def tickets_proxy(
    path: str,
    request: Request,
    authorization: Optional[str] = Depends(get_authorization_header)
):
    """Ticket service endpoints (requires authentication)"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Token'ı temizle (Bearer prefix'ini kaldır)
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Token doğrula
    get_current_user(token)
    
    return await proxy_request(
        settings.TICKET_SERVICE_URL,
        f"/api/v1/tickets/{path}",
        request.method,
        request
    )


# Payment Service Routes
@router.api_route("/payments/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def payments_proxy(
    path: str,
    request: Request,
    authorization: Optional[str] = Depends(get_authorization_header)
):
    """Payment service endpoints (requires authentication)"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = authorization.replace("Bearer ", "")
    get_current_user(token)
    
    return await proxy_request(
        settings.PAYMENT_SERVICE_URL,
        f"/api/v1/payments/{path}",
        request.method,
        request
    )


# Notification Service Routes
@router.api_route("/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def notifications_proxy(
    path: str,
    request: Request,
    authorization: Optional[str] = Depends(get_authorization_header)
):
    """Notification service endpoints (requires authentication)"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    token = authorization.replace("Bearer ", "")
    get_current_user(token)
    
    return await proxy_request(
        settings.NOTIFICATION_SERVICE_URL,
        f"/api/v1/notifications/{path}",
        request.method,
        request
    )

