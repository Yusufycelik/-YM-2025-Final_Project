import pika
import json
from app.config import settings


def get_connection():
    """RabbitMQ bağlantısı oluştur"""
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )
    return connection


def publish_message(exchange: str, routing_key: str, message: dict):
    """Mesaj yayınla"""
    connection = get_connection()
    channel = connection.channel()
    
    channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
    
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )
    
    connection.close()


def consume_messages(queue: str, callback):
    """Mesaj dinle"""
    connection = get_connection()
    channel = connection.channel()
    
    channel.queue_declare(queue=queue, durable=True)
    
    channel.basic_consume(
        queue=queue,
        on_message_callback=callback,
        auto_ack=True
    )
    
    channel.start_consuming()

