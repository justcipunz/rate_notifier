import os
import pika
import requests
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "https://www.cbr-xml-daily.ru/daily_json.js")
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", 60))

def get_dollar_rate():
    """Получает курс доллара с внешнего API."""
    try:
        response = requests.get(EXTERNAL_API_URL)
        response.raise_for_status()  
        data = response.json()
        rate = data['Valute']['USD']['Value']
        logging.info(f"Successfully fetched dollar rate: {rate}")
        return rate
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching rate from API: {e}")
    except KeyError:
        logging.error("Error parsing API response: 'USD' key not found.")
    return None

def main():
    """Главная функция: подключение к RabbitMQ и цикл публикации."""
    connection = None
    
    while True:
        try:
            logging.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}...")
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
            channel = connection.channel()
            
            exchange_name = 'rate_exchange'
            channel.exchange_declare(exchange=exchange_name, exchange_type='direct')
            
            logging.info("Successfully connected to RabbitMQ. Starting rate tracking.")
            
            while True:
                rate = get_dollar_rate()
                if rate is not None:
                    message = json.dumps({"rate": rate})
                    
                    channel.basic_publish(
                        exchange=exchange_name,
                        routing_key='rate.usd.updated', 
                        body=message
                    )
                    logging.info(f"Sent message to RabbitMQ: {message}")
                
                time.sleep(FETCH_INTERVAL_SECONDS)

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
