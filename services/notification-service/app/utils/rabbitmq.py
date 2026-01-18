import pika
import json
import logging
from app.config import settings

# Logger oluştur
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[NOTIFICATION_SERVICE] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_connection():
    """RabbitMQ bağlantısı oluştur"""
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )
    return connection


def consume_messages(queue: str, callback, routing_key: str = None):
    """Mesaj dinle - otomatik yeniden bağlanma ile"""
    import time
    
    retry_count = 0
    max_retries = 10
    retry_delay = 5  # saniye
    
    while retry_count < max_retries:
        try:
            logger.info(f"consume_messages called: queue={queue}, routing_key={routing_key}, attempt={retry_count + 1}")
            connection = get_connection()
            channel = connection.channel()
            
            logger.info("Declaring exchange 'notifications'...")
            channel.exchange_declare(exchange="notifications", exchange_type='topic', durable=True)
            
            logger.info(f"Declaring queue '{queue}'...")
            channel.queue_declare(queue=queue, durable=True)
            
            # Routing key belirtilmişse onu kullan, yoksa queue adından çıkar
            if routing_key:
                bind_key = routing_key
            else:
                # Queue adından routing key çıkar: "notification.payment.completed" -> "payment.completed"
                if queue.startswith("notification."):
                    bind_key = queue.replace("notification.", "")
                else:
                    bind_key = "#"  # Tüm mesajları al
            
            logger.info(f"Binding queue '{queue}' to exchange 'notifications' with routing_key '{bind_key}'...")
            channel.queue_bind(exchange="notifications", queue=queue, routing_key=bind_key)
            logger.info(f"Queue '{queue}' bound to routing_key '{bind_key}'")
            
            logger.info(f"Setting up consumer for queue '{queue}'...")
            
            # Wrapper callback to handle errors
            def wrapped_callback(ch, method, properties, body):
                try:
                    logger.info(f"Message received on queue '{queue}': {len(body)} bytes")
                    callback(ch, method, properties, body)
                    logger.info(f"Message processed successfully on queue '{queue}'")
                except Exception as e:
                    logger.error(f"Error processing message on queue '{queue}': {e}", exc_info=True)
                    # Don't re-raise, just log the error
            
            channel.basic_consume(
                queue=queue,
                on_message_callback=wrapped_callback,
                auto_ack=True
            )
            
            logger.info(f"Waiting for messages on queue: {queue}")
            retry_count = 0  # Başarılı bağlantıda retry sayacını sıfırla
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info(f"Consumer interrupted for queue: {queue}")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Error in consumer for queue '{queue}': {e}")
            logger.info(f"Retrying in {retry_delay} seconds... (attempt {retry_count}/{max_retries})")
            
            if retry_count < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries reached for queue '{queue}'. Consumer stopped.")
                break

