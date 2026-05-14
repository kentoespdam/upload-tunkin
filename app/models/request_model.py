from typing import Annotated, Optional

from fastapi import Depends, File, Form, UploadFile
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

    def __init__(
        self,
        periode: Annotated[str, Form()],
        file: UploadFile = File(...),
    ):
        self.periode = periode
        self.file = file
