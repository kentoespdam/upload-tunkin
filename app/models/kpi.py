"""KPIRecord model — represents a single row from the Excel upload."""
from pydantic import BaseModel, Field


class KPIRecord(BaseModel):
    """A single KPI data row parsed from the uploaded Excel file."""
    periode: str = Field(..., min_length=6, max_length=6)
    nipam: str = Field(..., min_length=8, max_length=9)
    tunkin: int
    pph21_ter: int

    class Config:
        frozen = True


class UpsertResult(BaseModel):
    """Summary returned after a bulk upsert operation."""
    status: str = "success"
    affected_rows: int = 0
