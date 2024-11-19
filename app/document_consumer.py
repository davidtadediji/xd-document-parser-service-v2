# document_consumer.py
from confluent_kafka import Consumer, KafkaError
from app.document_processor import DocumentProcessor
from app.log_producer import LogProducer
import json


class DocumentConsumer:
    def __init__(
            self,
            kafka_config: dict,
            topics: list,
            document_processor: DocumentProcessor,
            log_producer: LogProducer
    ):
        self.consumer = Consumer(kafka_config)
        self.consumer.subscribe(topics)
        self.document_processor = document_processor
        self.log_producer = log_producer
        self.shutdown_event = False

    async def handle_message(self, message):
        """
        Handle the received message by processing the document.
        """
        try:
            # Extract metadata from headers
            headers = dict(message.headers()) if message.headers() else {}

            # Process the document using DocumentProcessor
            file_content = message.value()
            filename = headers.get('filename', 'unknown_file')

            # Create a BytesIO object from the file content
            from io import BytesIO
            file_obj = BytesIO(file_content)

            # Process the document
            result = await self.document_processor.process_document(file_obj, filename)
            self.log_producer.log_info(f"Successfully processed document: {filename}")

            return result

        except Exception as e:
            self.log_producer.log_error(f"Error processing message: {str(e)}")
            # You might want to send to DLQ here
            raise

    async def consume_messages(self):
        """
        Consume messages from the Kafka topic.
        """
        try:
            while not self.shutdown_event:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        self.log_producer.log_info(
                            f"Reached end of partition {msg.partition()}"
                        )
                    else:
                        self.log_producer.log_error(
                            f"Error while consuming message: {msg.error()}"
                        )
                    continue

                try:
                    await self.handle_message(msg)
                    self.consumer.commit(msg)
                except Exception as e:
                    self.log_producer.log_error(
                        f"Error processing message: {str(e)}"
                    )
                    # Implement your error handling strategy here
                    # e.g., send to DLQ, skip, retry, etc.

        except Exception as e:
            self.log_producer.log_error(f"Error in consume_messages: {str(e)}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Handle shutdown signal to gracefully stop the consumer."""
        try:
            self.shutdown_event = True
            self.consumer.close()
            self.log_producer.log_info("Consumer shutdown complete.")
        except Exception as e:
            self.log_producer.log_error(f"Error during shutdown: {str(e)}")
