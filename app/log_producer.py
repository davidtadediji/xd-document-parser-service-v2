# log_producer.py
from confluent_kafka import Producer
import json
from datetime import datetime

class LogProducer:
    def __init__(self, kafka_config, topic):
        self.producer = Producer(kafka_config)
        self.topic = topic

    def produce_log(self, log_message: str, log_level: str):
        log_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "log_level": log_level,
            "message": log_message,
            "service": "document-parser"
        }

        try:
            self.producer.produce(self.topic, json.dumps(log_data).encode("utf-8"))
            self.producer.flush()
            print(f"Produced log message: {log_data}")
        except Exception as e:
            print(f"Error producing log message: {e}")

    def log_info(self, log_message: str):
        self.produce_log(log_message, log_level="INFO")

    def log_warning(self, log_message: str):
        self.produce_log(log_message, log_level="WARNING")

    def log_error(self, log_message: str):
        self.produce_log(log_message, log_level="ERROR")

    def cleanup(self):
        self.producer.flush()
        self.log_info("Kafka producer flush complete.")
