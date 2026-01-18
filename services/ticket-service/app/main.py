from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import asyncio
from datetime import datetime, timedelta
from app.database import get_db, engine, Base, SessionLocal
from app.routes import tickets
from app.config import settings
from app.services.ticket_consumer import start_consumers
from app.models import Ticket, TicketStatus
from app.utils.rabbitmq import publish_message

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ticket Service",
    description="Bilet yönetimi ve rezervasyon servisi",
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
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["Tickets"])

def check_reservation_timeouts():
    """Rezervasyon süresi dolmuş biletleri iptal et"""
    db = SessionLocal()
    try:
        timeout_threshold = datetime.utcnow() - timedelta(minutes=settings.RESERVATION_TIMEOUT_MINUTES)
        
        # Süresi dolmuş reserved ticket'ları bul
        expired_tickets = db.query(Ticket).filter(
            Ticket.status == TicketStatus.RESERVED,
            Ticket.reserved_at < timeout_threshold
        ).all()
        
        for ticket in expired_tickets:
            ticket.status = TicketStatus.CANCELLED
            ticket.cancelled_at = datetime.utcnow()
            
            # Event service'e stok geri verme mesajı gönder
            publish_message(
                exchange="events",
                routing_key="ticket.cancelled",
                message={
                    "event_id": ticket.event_id,
                    "quantity": ticket.quantity
                }
            )
            
            print(f"Ticket {ticket.id} cancelled due to reservation timeout")
        
        db.commit()
    except Exception as e:
        print(f"Error checking reservation timeouts: {e}")
        db.rollback()
    finally:
        db.close()


async def reservation_timeout_checker():
    """Rezervasyon timeout kontrolü için background task"""
    while True:
        try:
            await asyncio.sleep(60)  # Her 1 dakikada bir kontrol et
            check_reservation_timeouts()
        except Exception as e:
            print(f"Error in reservation timeout checker: {e}")


# Start RabbitMQ consumers in background
@app.on_event("startup")
async def startup_event():
    # RabbitMQ consumers
    thread = threading.Thread(target=start_consumers, daemon=True)
    thread.start()
    
    # Rezervasyon timeout kontrolü
    asyncio.create_task(reservation_timeout_checker())

@app.get("/")
async def root():
    return {
        "service": "ticket-service",
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
        port=8003,
        reload=True
    )

