from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel


class PaginationQuery(BaseModel):
    page: int = 1
    size: int = 10


class TunkinRequest(PaginationQuery):
    nipam: Optional[str] = None
    nama: Optional[str] = None
    orgId: Optional[str] = None


class TunkinUploadRequest:
    """Request model for Tunkin file upload with periode + file."""
    periode: str
    file: UploadFile
