from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas import Token, UserCreate, UserResponse
from app.services import user_service
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.redis import rate_limit_check
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Kullanıcı kaydı - Rate limiting: 5 kayıt/dakika/IP"""
    # IP adresini al - X-Forwarded-For header'ını kontrol et (API Gateway üzerinden geliyorsa)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # İlk IP adresini al (birden fazla proxy varsa)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"rate_limit:register:{client_ip}"
    
    # Rate limiting kontrolü: 5 kayıt / 60 saniye
    is_allowed, remaining = rate_limit_check(rate_limit_key, limit=5, window=60)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Çok fazla kayıt denemesi yaptınız. Lütfen 1 dakika bekleyin. Kalan deneme hakkı: {remaining}",
            headers={"Retry-After": "60"}
        )
    
    db_user = user_service.create_user(db, user)
    return db_user


@router.post("/login", response_model=Token)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı girişi - Rate limiting: 5 deneme/dakika/IP"""
    # IP adresini al - X-Forwarded-For header'ını kontrol et (API Gateway üzerinden geliyorsa)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # İlk IP adresini al (birden fazla proxy varsa)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"rate_limit:login:{client_ip}"
    
    # Rate limiting kontrolü: 5 deneme / 60 saniye
    is_allowed, remaining = rate_limit_check(rate_limit_key, limit=5, window=60)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Çok fazla giriş denemesi yaptınız. Lütfen 1 dakika bekleyin. Kalan deneme hakkı: {remaining}",
            headers={"Retry-After": "60", "WWW-Authenticate": "Bearer"}
        )
    
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.value,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Refresh token if valid manually"""
    if not form_data.scopes or "refresh_token" not in form_data.scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token scope required"
        )

    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role.value,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(lambda: None),  # This will be handled by API Gateway
    db: Session = Depends(get_db)
):
    """Mevcut kullanıcı bilgileri"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use API Gateway for authenticated endpoints"
    )
