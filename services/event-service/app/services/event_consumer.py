import json
import pika
from app.database import SessionLocal
from app.services.event_service import reserve_tickets, release_tickets
from app.config import settings


def get_connection():
    """RabbitMQ bağlantısı oluştur"""
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )
    return connection


def handle_ticket_reserved(ch, method, properties, body):
    """Bilet rezervasyonu mesajını işle"""
    try:
        message = json.loads(body)
        db = SessionLocal()
        try:
            reserve_tickets(db, message["event_id"], message["quantity"])
            print(f"Tickets reserved for event {message['event_id']}: {message['quantity']}")
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling ticket reserved: {e}")


def handle_ticket_cancelled(ch, method, properties, body):
    """Bilet iptali mesajını işle"""
    try:
        message = json.loads(body)
        db = SessionLocal()
        try:
            release_tickets(db, message["event_id"], message["quantity"])
            print(f"Tickets released for event {message['event_id']}: {message['quantity']}")
        finally:
            db.close()
    except Exception as e:
        print(f"Error handling ticket cancelled: {e}")


def start_consumers():
    """RabbitMQ consumer'ları başlat"""
    import time
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"Event Service: RabbitMQ'ya bağlanmaya çalışılıyor (deneme {attempt + 1}/{max_retries})...")
            connection = get_connection()
            channel = connection.channel()
            
            # Exchange oluştur
            channel.exchange_declare(exchange="events", exchange_type='topic', durable=True)
            
            # Queue'ları oluştur
            channel.queue_declare(queue="event.ticket.reserved", durable=True)
            channel.queue_declare(queue="event.ticket.cancelled", durable=True)
            
            # Queue binding
            channel.queue_bind(exchange="events", queue="event.ticket.reserved", routing_key="ticket.reserved")
            channel.queue_bind(exchange="events", queue="event.ticket.cancelled", routing_key="ticket.cancelled")
            
            # Consumer'ları başlat
            channel.basic_consume(queue="event.ticket.reserved", on_message_callback=handle_ticket_reserved, auto_ack=True)
            channel.basic_consume(queue="event.ticket.cancelled", on_message_callback=handle_ticket_cancelled, auto_ack=True)
            
            print("Event Service consumers started successfully!")
            channel.start_consuming()
            break
        except Exception as e:
            import traceback
            print(f"Error starting consumers (attempt {attempt + 1}): {type(e).__name__}: {e}")
            traceback.print_exc()
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Consumer could not start.")

