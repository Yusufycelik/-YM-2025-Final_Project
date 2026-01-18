from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.database import get_db, engine, Base
from app.routes import notifications
from app.config import settings
import threading
from app.services.notification_service import start_consumers

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Bildirim servisi",
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
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])

# Start RabbitMQ consumers in background - basit ve güvenilir yöntem
@app.on_event("startup")
async def startup_event():
    print("[NOTIFICATION_SERVICE] Startup event triggered!")
    print("[NOTIFICATION_SERVICE] Starting consumer threads...")
    consumer_thread = threading.Thread(target=start_consumers, daemon=True)
    consumer_thread.start()
    print(f"[NOTIFICATION_SERVICE] Consumer thread started: name={consumer_thread.name}")
    # Thread'in başlaması için kısa bir süre bekle
    import asyncio
    await asyncio.sleep(1.0)
    print(f"[NOTIFICATION_SERVICE] Startup complete - consumers should be running")

@app.get("/")
async def root():
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    )
