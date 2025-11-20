from pydantic import BaseModel


class PageResponse(BaseModel):
    data: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
