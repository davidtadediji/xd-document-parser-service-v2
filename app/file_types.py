# file_types.py
from enum import Enum

class FileType(Enum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PLAIN_TEXT = "text/plain"
    CSV = "text/csv"
    JSON = "application/json"
    XML = "application/xml"
    YAML = "application/x-yaml"
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    OLD_EXCEL = "application/vnd.ms-excel"
    POWERPOINT = "application/vnd.ms-powerpoint"
    HTML = "text/html"
    MARKDOWN = "text/markdown"
    RTF = "application/rtf"
    EPUB = "application/epub+zip"
    BIBTEX = "application/x-bibtex"
