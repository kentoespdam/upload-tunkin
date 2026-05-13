"""FileGate — validates an uploaded file and returns raw bytes.

No pandas or DB dependencies. Raises HTTPException on validation
failure to match the exact error shape of the original upload flow.
"""

from fastapi import UploadFile, HTTPException


ALLOWED_EXTENSIONS = {"xlsx", "xls"}
ALLOWED_MIME_TYPES = {
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MiB


class FileGate:
    """Validates file metadata and returns raw bytes for downstream parsing."""

    @staticmethod
    async def check(upload_file: UploadFile) -> bytes:
        """Validate extension / MIME / size and return bytes.

        Raises HTTPException with the same status + message as the
        pre-refactor monolith.
        """
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
