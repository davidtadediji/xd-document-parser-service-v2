# dependencies.py
from functools import lru_cache
from fastapi import Depends
from app.document_processor import DocumentProcessor
from app.object_storage import MinIOStorage
from app.temp_file_storage import TempFileStorage
from app.config import Settings
from app.log_producer import LogProducer

@lru_cache
def get_settings() -> Settings:
    """
    Returns a Settings instance, ensuring environment variables are loaded only once.
    """
    return Settings()

def get_log_producer(settings: Settings = Depends(get_settings)) -> LogProducer:
    """
    Returns a LogProducer instance using Kafka settings and topics from the config.
    """
    kafka_config = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
       }
    return LogProducer(kafka_config, settings.KAFKA_TOPICS[1])

def get_minio_storage(
    settings: Settings = Depends(get_settings),
    log_producer: LogProducer = Depends(get_log_producer)
) -> MinIOStorage:
    """
    Return a MinIOStorage instance configured with settings.
    """
    return MinIOStorage(settings=settings, log_producer=log_producer)

def get_temp_file_storage(
    log_producer: LogProducer = Depends(get_log_producer)
) -> TempFileStorage:
    """
    Return a TempFileStorage instance.
    """
    return TempFileStorage(log_producer=log_producer)

def get_document_processor(
    minio_storage: MinIOStorage = Depends(get_minio_storage),
    temp_file_storage: TempFileStorage = Depends(get_temp_file_storage),
    log_producer: LogProducer = Depends(get_log_producer)
) -> DocumentProcessor:
    """
    Provide a DocumentProcessor with all required dependencies.
    """
    return DocumentProcessor(
        storage=minio_storage,
        temp_file_storage=temp_file_storage,
        log_producer=log_producer
    )
