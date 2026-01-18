from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Ticket Service settings and configuration
    """
    # Service Info
    SERVICE_NAME: str = "ticket-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@ticket-db:5432/ticketdb"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # External Services
    EVENT_SERVICE_URL: str = os.getenv("EVENT_SERVICE_URL", "http://event-service:8002")
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8004")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
    
    # JWT Settings (shared with User Service / API Gateway)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-12345")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Business Rules
    MAX_TICKETS_PER_USER_PER_EVENT: int = int(os.getenv("MAX_TICKETS_PER_USER_PER_EVENT", "5"))
    RESERVATION_TIMEOUT_MINUTES: int = int(os.getenv("RESERVATION_TIMEOUT_MINUTES", "15"))
    
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

