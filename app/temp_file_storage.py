# temp_file_storage.py
import os
import tempfile
import zipfile
import shutil
from fastapi import UploadFile
from typing import List, Union
import asyncio
from io import BytesIO
from app.base import BaseFileStorage
from app.log_producer import LogProducer


class TempFileStorage(BaseFileStorage):

    def __init__(self, log_producer: LogProducer):
        self.saved_file = []  # Track all saved/extracted file paths (file.name, file.temp_path)
        self.log_producer = log_producer

    def is_zip_file(self, file: Union[UploadFile, BytesIO]) -> bool:
        """Check if the provided file or BytesIO object is a ZIP file by reading its first 4 bytes."""
        try:
            if isinstance(file, UploadFile):
                file_content = file.file.read(4)
                if len(file_content) < 4:
                    raise ValueError("Incomplete file data")
                return file_content == b'\x50\x4B\x03\x04'

            elif isinstance(file, BytesIO):
                file_content = file.read(4)
                if len(file_content) < 4:
                    raise ValueError("Incomplete file data")
                return file_content == b'\x50\x4B\x03\x04'

        except Exception as e:
            self.log_producer.log_error(f"Error checking if file is a ZIP: {e}")
            return False

    async def save_file(self, file: Union[UploadFile, BytesIO], filename: str = None) -> str:
        """Save a regular (non-ZIP) file to temporary storage."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            if isinstance(file, UploadFile):
                content = await file.read()
                tmp.write(content)
                temp_file_path = tmp.name

                # Preserve file metadata (e.g., timestamps) for UploadFile
                if file.filename and hasattr(file, 'file'):
                    shutil.copystat(file.file.name, temp_file_path)  # This copies timestamps and permissions

                self.log_producer.log_info(f"Saved file at {temp_file_path}")
            elif isinstance(file, BytesIO):
                content = file.read()
                tmp.write(content)
                temp_file_path = tmp.name

            # Append the file path to the saved file paths list (track file name and saved path)
            self.saved_file.append({"file_name": filename or "unknown", "temp_path": temp_file_path})
        return temp_file_path

    async def save_files(self, files: List[Union[UploadFile, BytesIO]]) -> List[dict]:
        """Save multiple files and determine whether to extract or save based on the file type."""
        await asyncio.gather(*[self.save_or_extract_file(file) for file in files])

        # Return the updated saved_file after processing, now containing file name and temp path
        return self.saved_file

    async def save_or_extract_file(self, file: Union[UploadFile, BytesIO]):
        """Check if the file is a ZIP file and either extract or save accordingly."""
        if self.is_zip_file(file):
            # If it's a ZIP file, extract its contents
            file_content = await file.read() if isinstance(file, UploadFile) else file.read()
            extracted_files = await self.extract_zip(file, file_content)
            self.saved_file.extend(extracted_files)
        else:
            # Otherwise, save it as a regular file
            saved_file = await self.save_file(file)
            self.saved_file.append({"file_name": file.filename or "unknown", "temp_path": saved_file})

    async def extract_zip(self, file: Union[UploadFile, BytesIO], file_content: bytes) -> List[dict]:
        """Extract the contents of a ZIP file from either UploadFile or BytesIO."""
        extracted_files = []
        try:
            extracted_files = await asyncio.to_thread(self._extract_zip, file, file_content)
        except Exception as e:
            self.log_producer.log_error(f"Error extracting ZIP file: {e}")
        return extracted_files

    def _extract_zip(self, file: Union[UploadFile, BytesIO], file_content: bytes) -> List[dict]:
        """Extract the contents of a ZIP file (synchronous method to be run in a separate thread)."""
        extracted_files = []
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_zip_path = os.path.join(temp_dir, 'temp_zip.zip')
                with open(temp_zip_path, 'wb') as temp_zip_file:
                    temp_zip_file.write(file_content)

                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                    # Store the paths of the extracted files
                    for file in zip_ref.namelist():
                        extracted_file_path = os.path.join(temp_dir, file)
                        extracted_files.append({"file_name": file, "temp_path": extracted_file_path})

                    # Optionally preserve metadata for extracted files (only for UploadFile)
                    if isinstance(file, UploadFile) and file.filename:
                        for extracted_file in extracted_files:
                            shutil.copystat(temp_zip_path, extracted_file["temp_path"])

        except zipfile.BadZipFile:
            self.log_producer.log_error(f"Error: The provided byte data is not a valid ZIP file.")
        except Exception as e:
            self.log_producer.log_error(f"Error extracting ZIP file: {e}")

        return extracted_files
