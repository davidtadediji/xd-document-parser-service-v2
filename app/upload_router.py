# upload_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.document_processor import DocumentProcessor
from app.log_producer import LogProducer
from app.dependencies import get_log_producer, get_document_processor
from typing import List

router = APIRouter()


@router.post("/upload/")
async def process_documents(
        # files: List[UploadFile] = File(...),
        document_processor: DocumentProcessor = Depends(get_document_processor),
        log_producer: LogProducer = Depends(get_log_producer)
):
    """
    Endpoint to upload a document, store it in MinIO, and log the action.
    """
    try:
        raise
        # Upload document using the processor service
        # await document_processor.process_documents(files)
        #
        # # Log the successful upload
        # log_producer.log_info(f"Documents uploaded successfully")
        #
        # return {"message": f"Documents uploaded successfully"}
    except Exception as e:
        # Log the error
        log_producer.log_error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")
