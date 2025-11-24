from typing import Optional

from pydantic import BaseModel


class PaginationQuery(BaseModel):
    page: int = 1
    size: int = 10


class TunkinRequest(PaginationQuery):
    nipam: Optional[str] = None

