# document_processor.py
from io import BytesIO
from typing import Union, List

import filetype
from fastapi import UploadFile
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    BSHTMLLoader,
    UnstructuredMarkdownLoader, UnstructuredRTFLoader, UnstructuredEPubLoader, BibtexLoader,
)

from app.file_types import FileType
from app.log_producer import LogProducer
from app.object_storage import MinIOStorage
from app.temp_file_storage import TempFileStorage

# Type alias for loaders that have a 'load' method
DocumentLoader = Union[
    PyMuPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    BSHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredRTFLoader,
    UnstructuredEPubLoader,
    BibtexLoader,
]


class DocumentProcessor:
    def __init__(self, storage: MinIOStorage, temp_file_storage: TempFileStorage, log_producer: LogProducer):
        """
        Initialize the DocumentProcessor with a storage backend, temporary file storage, and a log producer.
        """
        self.storage = storage
        self.temp_file_storage = temp_file_storage
        self.log_producer = log_producer

    @staticmethod
    def _get_document_loader(file_path: str, file_content: bytes) -> DocumentLoader:
        """
        Select the appropriate LangChain document loader based on the file type determined by 'filetype' library.
        """
        try:
            # Detect file type using filetype library
            kind = filetype.guess(file_content)

            if kind is None:
                raise ValueError(f"Unable to detect file type for {file_path}.")

            mime_type = kind.mime

            # Map MIME types to their corresponding document loaders
            if mime_type == FileType.PDF.value:
                return PyMuPDFLoader(file_path)
            elif mime_type == FileType.DOCX.value:
                return UnstructuredWordDocumentLoader(file_path)
            elif mime_type == FileType.PLAIN_TEXT.value:
                return TextLoader(file_path)
            elif mime_type == FileType.CSV.value:
                return CSVLoader(file_path)
            elif mime_type == FileType.JSON.value:
                return JSONLoader(file_path, jq_schema="")
            elif mime_type == FileType.XML.value:
                return UnstructuredXMLLoader(file_path)
            elif mime_type == FileType.YAML.value:
                return TextLoader(file_path)
            elif mime_type in [FileType.EXCEL.value, FileType.OLD_EXCEL.value]:
                return UnstructuredExcelLoader(file_path)
            elif mime_type == FileType.POWERPOINT.value:
                return UnstructuredPowerPointLoader(file_path)
            elif mime_type == FileType.HTML.value:
                return BSHTMLLoader(file_path)
            elif mime_type == FileType.MARKDOWN.value:
                return UnstructuredMarkdownLoader(file_path)
            elif mime_type == FileType.RTF.value:
                return UnstructuredRTFLoader(file_path)
            elif mime_type == FileType.EPUB.value:
                return UnstructuredEPubLoader(file_path)
            elif mime_type == FileType.BIBTEX.value:
                return BibtexLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type detected: {mime_type}")
        except Exception as e:
            raise ValueError(f"Failed to select document loader for {file_path}") from e

    async def process_documents(self, files: List[Union[UploadFile, BytesIO]]):
        """
        Process a list of documents by saving them, selecting the appropriate loader,
        and storing the processed document in storage.
        """
        try:
            # Step 1: Save all files using TempFileStorage
            saved_file_paths = await self.temp_file_storage.save_files(files)
            print(saved_file_paths)

            # Step 2: Process each saved file
            for saved_file in saved_file_paths:  # Use saved_file instead of zip
                file_name = saved_file['file_name']  # Extract file name
                temp_path = saved_file['temp_path']  # Extract the temporary file path
                await self.process_document(temp_path, file_name)  # Pass filename along with temp path

        except Exception as e:
            # Log a general error message with the exception details
            raise Exception(f"Failed to process documents --> {str(e)}")

    async def process_document(self, temp_path: str, filename: str) -> str:
        # print(temp_path, filename)
        """
        Process a single document by loading it, serializing, and uploading to storage.

        Args:
        - saved_file_path (str): The path where the file is stored temporarily.
        - filename (str): The name of the file.

        Returns:
        - str: A success message indicating the file was processed and uploaded successfully.
        """
        try:
            # Read the file content to detect its type
            with open(temp_path, "rb") as f:
                file_content = f.read()

            # Step 1: Load the document using the appropriate loader
            loader = self._get_document_loader(temp_path, file_content)
            if loader is None:
                raise ValueError(f"Failed to load document: {filename}")
            documents = loader.load()  # This will load a list of Document objects

            # Step 2: Process each document and serialize them
            serialized_documents = []
            for document in documents:
                # Ensure we're working with a Document object, which supports the 'serialize' method
                if hasattr(document, 'serialize'):
                    serialized_documents.append(document.serialize())
                else:
                    raise ValueError("The loaded content is not a valid Document object.")

            # Step 3: Combine all serialized document data if needed (here assuming they're all concatenated)
            combined_serialized_document = b''.join(serialized_documents)

            # Step 4: Create a byte stream from the serialized document
            file_stream = BytesIO(combined_serialized_document)

            # Step 5: Set metadata for the file (Content-Type can be adjusted based on your needs)
            metadata = {"Content-Type": "application/octet-stream"}  # Example metadata, adjust as needed

            # Step 6: Upload the processed document to MinIOStorage
            self.storage.store_document(
                object_name=filename,
                metadata=metadata,
                content=file_stream,
                size=len(combined_serialized_document),
            )

            # Step 7: log a success message
            self.log_producer.log_info(f"Document '{filename}' uploaded successfully to storage.")

        except Exception as e:
            # Log a general error message for failed document processing
            raise Exception(f"Failed to process document: {filename} --> {e}")

    def get_document_url(self, file_name: str) -> str:
        """
        Generate a pre-signed URL for the document in the storage backend.
        """
        try:
            return self.storage.minio.presigned_get_object(
                self.storage.bucket, file_name
            )
        except Exception as e:
            raise Exception(f"Failed to generate URL for {file_name}") from e
