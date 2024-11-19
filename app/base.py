from abc import ABC, abstractmethod
from typing import Dict, Any
from typing import BinaryIO
from typing import Union
from fastapi import UploadFile
from typing import List

from pathlib import Path
from io import BufferedReader, BytesIO


class ObjectStorage(ABC):
    @abstractmethod
    def store_document(
            self,
            object_name: str,
            metadata: Dict[str, Any],
            content: Union[BinaryIO, bytes],
            size: int,
    ) -> None:
        """
        Upload a document to the storage system.

        This is an abstract method that must be implemented by subclasses to store a document
        in the storage system (e.g., S3, MinIO). The content can either be a file-like object or raw byte data.

        Parameters:
        - object_name (str): The name of the object (file) to store in the storage system.
        - metadata (dict): A dictionary containing metadata associated with the object.
        - content (Union[BinaryIO, bytes]): The content of the document to upload. This can either be
          a file-like object (BinaryIO) or raw byte data (bytes).
        - size (int): The size of the content in bytes.

        Returns:
        - None
        """
        pass

    @abstractmethod
    def download_document(
            self, object_name: str, offset: int = 0, size: int = 0
    ) -> None:
        """
        Download a document from the storage system.

        This is an abstract method that must be implemented by subclasses to download a document
        from the storage system. The `offset` and `size` parameters allow partial downloads.

        Parameters:
        - object_name (str): The name of the object (file) to download.
        - offset (int, optional): The starting byte position from where the download should begin. Defaults to 0.
        - size (int, optional): The number of bytes to download from the offset. Defaults to 0, indicating the entire object.

        Returns:
        - None
        """
        pass

    @abstractmethod
    def delete_document(self, object_name: str) -> bool:
        """
        Delete a document from the storage system.

        This is an abstract method that must be implemented by subclasses to delete an object
        from the storage system.

        Parameters:
        - object_name (str): The name of the object (file) to delete.

        Returns:
        - bool: Returns True if the document was successfully deleted, False otherwise.
        """
        pass


class BaseFileStorage(ABC):
    """
    Abstract base class for file storage operations.
    This class defines essential methods that any file storage implementation should follow.
    It supports multiple types of file-like objects using the Union type.
    """

    @abstractmethod
    def save_file(self, file: Union[UploadFile, Path, BufferedReader]) -> str:
        """
        Save a single uploaded file or any other file-like object (e.g., file from disk).

        Parameters:
        - file (Union[UploadFile, Path, BufferedReader]): The file to be saved. It can be a FastAPI UploadFile,
          a Path object, or any file-like object.

        Returns:
        - str: The path to the saved file.
        """
        pass

    @abstractmethod
    async def extract_zip(self, file: Union[UploadFile, BytesIO], file_content: bytes) -> List[str]:
        """
        Extract files from a ZIP archive.

        Parameters:
        - file (Union[UploadFile, BytesIO]): The ZIP file to extract files from.
        - file_content (bytes): The byte content of the ZIP file.

        Returns:
        - List[str]: A list of paths to the extracted files.
        """
        pass

    @abstractmethod
    def save_files(
            self, files: List[Union[UploadFile, Path, BufferedReader]]
    ) -> List[str]:
        """
        Save multiple files from different sources.

        Parameters:
        - files (List[Union[UploadFile, Path, BufferedReader]]): A list of file-like objects to be saved.

        Returns:
        - List[str]: A list of paths to the saved files.
        """
        pass

    def clean_up(self) -> None:
        """
        Clean up temporary files or perform necessary file deletions after processing.

        This method is optional and can be overridden by subclasses if needed.
        """
        pass
