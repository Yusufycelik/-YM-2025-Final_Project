from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Payment Service settings and configuration
    """
    # Service Info
    SERVICE_NAME: str = "payment-service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@payment-db:5432/paymentdb"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/3")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # External Services
    TICKET_SERVICE_URL: str = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8003")
    
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

