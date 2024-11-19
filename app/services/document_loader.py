# import mimetypes
# from pathlib import Path
#
# from langchain_community.document_loaders import (
#     TextLoader,
#     CSVLoader,
#     UnstructuredImageLoader,
#     UnstructuredMarkdownLoader,
#     UnstructuredTSVLoader,
#     PyPDFLoader,
# )
# from app.log_producer import LogProducer
#
# class DocumentLoader:
#     def __init__(self, file_path: str, log_producer: LogProducer):
#         """
#         Initialize the DocumentLoader with the file path and log producer.
#         """
#         self.file_path = file_path
#         self.file_name = Path(file_path).name
#         self.file_type = self._detect_file_type()
#         self.loader = self._get_loader()
#         self.log_producer = log_producer
#
#     def _detect_file_type(self):
#         """
#         Detect the MIME type of the file using mimetypes.
#         If detection fails, raise an exception to be handled at a higher level.
#         """
#         mime_type, _ = mimetypes.guess_type(self.file_path)
#         if not mime_type:
#             raise ValueError(f"Failed to detect MIME type for {self.file_name}")
#         return mime_type
#
#     def _get_loader(self):
#         """
#         Determine the appropriate LangChain document loader based on the MIME type.
#         """
#         file_type = self.file_type.lower()
#
#         if "text/plain" in file_type:
#             return TextLoader(self.file_path)
#         elif "text/csv" in file_type:
#             return CSVLoader(self.file_path)
#         elif "text/tab-separated-values" in file_type:
#             return UnstructuredTSVLoader(self.file_path)
#         elif "application/pdf" in file_type:
#             return PyPDFLoader(self.file_path)
#         elif "image" in file_type:
#             return UnstructuredImageLoader(self.file_path)
#         elif "text/markdown" in file_type:
#             return UnstructuredMarkdownLoader(self.file_path)
#         else:
#             raise ValueError(f"Unsupported file type: {file_type}")
#
#     def load_document(self):
#         """
#         Load the document using the appropriate loader.
#         Logs and handles errors at this level, while intermediate methods just raise them.
#         """
#         try:
#             self.log_producer.log_info(
#                 f"Started loading document {self.file_name} with content type {self.file_type}"
#             )
#             documents = self.loader.load()
#             self.log_producer.log_info(f"Successfully loaded document {self.file_name}")
#             return documents
#         except ValueError as e:
#             self.log_producer.log_error(f"Error loading {self.file_name}: {str(e)}")
#             return None  # Safe result, no document loaded
#         except Exception as e:
#             # Log only once at the top level, no need to re-log if propagated
#             self.log_producer.log_error(
#                 f"Unexpected error loading {self.file_name}: {str(e)}"
#             )
#             raise  # Propagate the exception upwards
