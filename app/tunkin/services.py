"""FileGate and KPISheetParser — consolidated in one file.

FileGate validates uploaded file metadata and returns raw bytes.
KPISheetParser parses Excel bytes into validated KPIRecord list.
"""

import io
from typing import Optional

import pandas as pd
from fastapi import UploadFile, HTTPException

from app.tunkin.schemas import KPIRecord


ALLOWED_EXTENSIONS = {"xlsx", "xls"}
ALLOWED_MIME_TYPES = {
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MiB

TEMPLATE_COLUMNS = [
    "NO",
    "PERIODE",
    "NIPAM",
    "JUMLAH PENERIMAAN",
    "PPH21 TER"
]


# ── File Gate ─────────────────────────────────────────────────

class FileGate:
    """Validates file metadata and returns raw bytes for downstream parsing."""

    @staticmethod
    async def check(upload_file: UploadFile) -> bytes:
        if not upload_file:
            raise HTTPException(status_code=400, detail="File tidak ditemukan")

        if not upload_file.filename:
            raise HTTPException(status_code=400, detail="Nama File tidak valid")

        ext = upload_file.filename.lower().rsplit(".", 1)[-1] if "." in upload_file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Ekstensi file tidak diizinkan. Hanya ekstensi {', '.join(ALLOWED_EXTENSIONS)} yang diperbolehkan.",
            )

        if upload_file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Tipe konten file tidak valid untuk file Excel.",
            )

        contents = await upload_file.read()
        size = len(contents)

        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Ukuran file melebihi batas maksimum {MAX_FILE_SIZE / (1024 * 1024)} MB.",
            )

        if size == 0:
            raise HTTPException(status_code=400, detail="File Kosong")

        return contents


def get_file_gate() -> FileGate:
    return FileGate()


# ── KPI Sheet Parser ──────────────────────────────────────────

class KPISheetParser:
    """Parses KPI Excel data from raw bytes into validated records."""

    @staticmethod
    def parse(data: bytes, column_spec: list[str] | None = None) -> list[KPIRecord]:
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
        df["NIPAM"] = df["NIPAM"].astype(str).str.zfill(9)

        records: list[KPIRecord] = []
        for _, row in df.iterrows():
            records.append(
                KPIRecord(
                    periode=str(row["PERIODE"]),
                    nipam=str(row["NIPAM"]),
                    tunkin=int(row["JUMLAH PENERIMAAN"]),
                    pph21_ter=int(row["PPH21 TER"])
                )
            )

        return records


def get_kpi_sheet_parser() -> KPISheetParser:
    return KPISheetParser()