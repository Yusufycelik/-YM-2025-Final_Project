import json
import pika
from datetime import datetime
from app.database import SessionLocal
from app.models import Ticket, TicketStatus
from app.config import settings


def get_connection():
    """RabbitMQ bağlantısı oluştur"""
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )
    return connection


def handle_payment_completed(ch, method, properties, body):
    """Ödeme tamamlandı mesajını işle"""
    try:
        message = json.loads(body)
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == message["ticket_id"]).first()
            if ticket:
                ticket.status = TicketStatus.CONFIRMED
                ticket.payment_id = message["payment_id"]
                ticket.confirmed_at = datetime.utcnow()
                db.commit()
                print(f"Ticket {ticket.id} confirmed after payment")
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling payment completed: {e}")


def handle_payment_failed(ch, method, properties, body):
    """Ödeme başarısız mesajını işle - Bilet'i iptal et"""
    try:
        message = json.loads(body)
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == message["ticket_id"]).first()
            if ticket and ticket.status == TicketStatus.RESERVED:
                ticket.status = TicketStatus.CANCELLED
                ticket.cancelled_at = datetime.utcnow()
                db.commit()
                
                # Event service'e stok geri verme mesajı gönder
                from app.utils.rabbitmq import publish_message
                publish_message(
                    exchange="events",
                    routing_key="ticket.cancelled",
                    message={
                        "event_id": ticket.event_id,
                        "quantity": ticket.quantity
                    }
                )
                print(f"Ticket {ticket.id} cancelled due to payment failure")
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling payment failed: {e}")


def start_consumers():
    """RabbitMQ consumer'ları başlat"""
    try:
        connection = get_connection()
        channel = connection.channel()
        
        # Exchange oluştur
        channel.exchange_declare(exchange="tickets", exchange_type='topic', durable=True)
        
        # Queue'ları oluştur
        channel.queue_declare(queue="ticket.payment.completed", durable=True)
        channel.queue_declare(queue="ticket.payment.failed", durable=True)
        
        # Queue binding
        channel.queue_bind(exchange="tickets", queue="ticket.payment.completed", routing_key="payment.completed")
        channel.queue_bind(exchange="tickets", queue="ticket.payment.failed", routing_key="payment.failed")
        
        # Consumer'ları başlat
        channel.basic_consume(queue="ticket.payment.completed", on_message_callback=handle_payment_completed, auto_ack=True)
        channel.basic_consume(queue="ticket.payment.failed", on_message_callback=handle_payment_failed, auto_ack=True)
        
        print("Ticket Service consumers started")
        channel.start_consuming()
    except Exception as e:
        print(f"Error starting consumers: {e}")

