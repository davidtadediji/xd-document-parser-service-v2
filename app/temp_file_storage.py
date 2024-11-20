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
        self.saved_files = []  # Track all saved/extracted file paths (file.name, file.temp_path)
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
            raise Exception(f"Failed to check if file is a ZIP: {e}")

    async def save_file(self, file: Union[UploadFile, BytesIO], filename: str = None) -> str:
        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                # Specific type checking
                if type(file).__name__ == 'UploadFile':
                    self.log_producer.log_info("Saving UploadFile")
                    content = await file.read()
                    tmp.write(content)
                    temp_file_path = tmp.name
                    filename = filename or file.filename
                elif type(file).__name__ == 'BytesIO':
                    self.log_producer.log_info("Saving BytesIO")
                    content = file.read()
                    tmp.write(content)
                    temp_file_path = tmp.name
                else:
                    raise ValueError(f"Unsupported file type: {type(file)}")

                # Track the file in saved_files
                self.saved_files.append({
                    "file_name": filename or "unknown",
                    "temp_path": temp_file_path
                })

        except Exception as e:
            raise Exception(f"Failed to save document {filename} to temporary storage --> {e}")

        if not temp_file_path:
            raise ValueError("Temporary file path is empty after save operation.")

        return temp_file_path


    async def save_files(self, files: List[Union[UploadFile, BytesIO]]) -> List[dict]:
        """Save multiple files and determine whether to extract or save based on the file type with error handling."""
        try:
            # Using asyncio.gather to process all files concurrently
            await asyncio.gather(*[self.save_or_extract_file(file) for file in files])

        except Exception as e:
            raise Exception(f"Failed to store documents in temporary storage --> {e}")

        # Return the updated saved_files list after processing
        return self.saved_files

    async def save_or_extract_file(self, file: Union[UploadFile, BytesIO]):
        """Decides whether to save the file or extract it based on the file type."""
        # print(file)
        try:
            # Here, you should have the logic to either save or extract the file.
            # For example, if it's a ZIP file, extract it; otherwise, save it.
            await self.save_file(file, file.filename)  # Assuming this function is implemented elsewhere



        except Exception as e:
            raise Exception(f"Failed to save/extract document to temporary storage --> {str(e)}")

    async def extract_zip(self, file: Union[UploadFile, BytesIO], file_content: bytes) -> List[dict]:
        """Extract the contents of a ZIP file from either UploadFile or BytesIO."""
        try:
            extracted_files = await asyncio.to_thread(self._extract_zip, file, file_content)
        except Exception as e:
            raise Exception(f"Failed to extract ZIP file: {e}")
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
            raise Exception("Failed to extract ZIP: The provided byte data is not a valid ZIP file.")
        except Exception as e:
            raise Exception(f"Failed to extract ZIP file: {e}")

        return extracted_files
