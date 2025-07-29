import os
import pika
import time
import json
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/app_db").replace("+asyncpg", "")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def process_new_rate(rate: float):
    """
    Основная бизнес-логика: проверяет отметки и "отправляет" уведомления.
    """
    logging.info(f"Processing new rate: {rate}")
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, user_id, target_rate, condition 
            FROM rate_marks 
            WHERE is_active = TRUE AND 
                  ((condition = 'above' AND :rate >= target_rate) OR 
                   (condition = 'below' AND :rate <= target_rate))
        """)
        
        result = db.execute(query, {"rate": rate})
        triggered_marks = result.fetchall()

        if not triggered_marks:
            logging.info("No marks triggered by this rate.")
            return

        for mark in triggered_marks:
            
            logging.info(
                f"NOTIFICATION: User {mark.user_id} should be notified! "
                f"Rate {rate} crossed the mark '{mark.condition} {mark.target_rate}'."
            )

            update_query = text("UPDATE rate_marks SET is_active = FALSE WHERE id = :mark_id")
            db.execute(update_query, {"mark_id": mark.id})
        db.commit()
        logging.info(f"Processed and deactivated {len(triggered_marks)} marks.")

    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Главная функция: подключение к RabbitMQ и запуск потребителя (consumer)."""
    connection = None
    while True:
        try:
            logging.info(f"Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()

            exchange_name = 'rate_exchange'
            channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            
            channel.queue_bind(
                exchange=exchange_name, queue=queue_name, routing_key='rate.usd.updated'
            )

            def callback(ch, method, properties, body):
                """Функция, которая вызывается при получении сообщения."""
                logging.info(f"Received message: {body.decode()}")
                try:
                    data = json.loads(body)
                    rate = float(data['rate'])
                    process_new_rate(rate)
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logging.error(f"Could not process message: {e}")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            
            logging.info("Successfully connected and waiting for messages.")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"RabbitMQ connection failed: {e}. Retrying in 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            break
        finally:
            if connection and connection.is_open:
                connection.close()

if __name__ == "__main__":
    main()
