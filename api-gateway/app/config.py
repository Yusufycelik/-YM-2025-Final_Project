from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import os
import json


def flexible_json_loads(value: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


class Settings(BaseSettings):
    """
    API Gateway settings and configuration
    """
    # Service Info
    SERVICE_NAME: str = "api-gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-12345")
    JWT_ALGORITHM: str = "HS256"
    
    # Service URLs
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    EVENT_SERVICE_URL: str = os.getenv("EVENT_SERVICE_URL", "http://event-service:8002")
    TICKET_SERVICE_URL: str = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8003")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8004")
    NOTIFICATION_SERVICE_URL: str = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8005")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Allow env strings like 'http://a,http://b' for CORS origins."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        json_loads=flexible_json_loads,
        env_ignore_empty=True
    )


settings = Settings()
