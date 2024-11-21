from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_GROUP_ID: str = "documents-consumer-group"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_ENABLE_AUTO_COMMIT: bool = True
    KAFKA_MAX_POLL_INTERVAL_MS: int = 300000
    KAFKA_SESSION_TIMEOUT_MS: int = 30000

    # Kafka Topics for documents
    KAFKA_TOPICS: List[str]  # Pydantic will automatically parse the list from the .env
    KAFKA_DLQ_TOPIC_NAME: str

    # MinIO Configuration
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET: str = "documents"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = ""
    MINIO_AUTO_CREATE_BUCKET: bool = True

    # For backwards compatibility if needed
    @property
    def minio_endpoint(self) -> str:
        """
        Constructs the MinIO endpoint from host and port.
        """
        return f"{self.MINIO_HOST}:{self.MINIO_PORT}"

    class Config:
        env_file = ".env"
        case_sensitive = True