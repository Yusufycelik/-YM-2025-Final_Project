from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Event Service settings and configuration
    """
    # Service Info
    SERVICE_NAME: str = "event-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@event-db:5432/eventdb"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/1")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # JWT Settings (shared with User Service / API Gateway)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-12345")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

