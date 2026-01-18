from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.config import settings


def verify_token(token: str) -> dict:
    """JWT token doğrula"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str) -> dict:
    """Token'dan kullanıcı bilgilerini çıkar"""
    payload = verify_token(token)
    return payload

