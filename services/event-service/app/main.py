from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import threading
from app.database import get_db, engine, Base
from app.routes import events
from app.config import settings
from app.services.event_consumer import start_consumers

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Event Service",
    description="Etkinlik yönetimi servisi",
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
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])

# Start RabbitMQ consumers in background
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=start_consumers, daemon=True)
    thread.start()

@app.get("/")
async def root():
    return {
        "service": "event-service",
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
        port=8002,
        reload=True
    )

