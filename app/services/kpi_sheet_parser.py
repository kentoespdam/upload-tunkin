"""KPISheetParser — parses Excel bytes into a list of KPIRecord.

No FastAPI or DB dependencies. Pure pandas + Pydantic.
"""
import io

import pandas as pd
from fastapi import HTTPException

from app.models.kpi import KPIRecord


TEMPLATE_COLUMNS = [
    "NO",
    "PERIODE",
    "NIPAM",
    "JUMLAH PENERIMAAN",
]


class KPISheetParser:
    """Parses KPI Excel data from raw bytes into validated records."""

    def parse(self, data: bytes, column_spec: list[str] | None = None) -> list[KPIRecord]:
        """Read Excel bytes, validate shape, return list of KPIRecord."""
        required = column_spec or TEMPLATE_COLUMNS
        file_like = io.BytesIO(data)

        try:
            df = pd.read_excel(file_like)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Terjadi kesalahan saat memproses file Excel: {exc}",
            )

        if df.empty:
            raise HTTPException(status_code=400, detail="File Excel kosong")

        for col in required:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Kolom '{col}' tidak ditemukan dalam file Excel.",
                )

        df["PERIODE"] = df["PERIODE"].astype(str).str.zfill(6)
        df["NIPAM"] = df["NIPAM"].astype(str).str.zfill(8)

        records: list[KPIRecord] = []
        for _, row in df.iterrows():
            records.append(
                KPIRecord(
                    periode=str(row["PERIODE"]),
                    nipam=str(row["NIPAM"]),
                    nominal=int(row["JUMLAH PENERIMAAN"]),
                )
            )

        return records


def get_kpi_sheet_parser() -> KPISheetParser:
    return KPISheetParser()
