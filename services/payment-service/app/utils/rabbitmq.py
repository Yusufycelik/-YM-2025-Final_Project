import pika
import json
from datetime import datetime
from app.config import settings


def get_connection():
    """RabbitMQ bağlantısı oluştur"""
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )
    return connection


def publish_message(exchange: str, routing_key: str, message: dict):
    """Mesaj yayınla"""
    try:
        connection = get_connection()
        channel = connection.channel()
        
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        
        message_body = json.dumps(message)
        timestamp = datetime.utcnow().isoformat()
        print(f"[PAYMENT_SERVICE] [{timestamp}] Publishing message to exchange='{exchange}', routing_key='{routing_key}'")
        print(f"[PAYMENT_SERVICE] [{timestamp}] Message content: {message_body}")
        
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        
        print(f"[PAYMENT_SERVICE] [{timestamp}] Message published successfully to {exchange}/{routing_key}")
        connection.close()
    except Exception as e:
        print(f"[PAYMENT_SERVICE] Error publishing message to {exchange}/{routing_key}: {e}")
        import traceback
        traceback.print_exc()

