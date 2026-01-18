from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from app.config import settings
from app.utils.auth import verify_token
from app.routes import gateway

app = FastAPI(
    title="API Gateway",
    description="Merkezi API giriş noktası",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gateway.router, prefix="/api/v1", tags=["Gateway"])

@app.get("/")
async def root():
    return {
        "service": "api-gateway",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "user-service": settings.USER_SERVICE_URL,
            "event-service": settings.EVENT_SERVICE_URL,
            "ticket-service": settings.TICKET_SERVICE_URL,
            "payment-service": settings.PAYMENT_SERVICE_URL,
            "notification-service": settings.NOTIFICATION_SERVICE_URL
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

