from fastapi import UploadFile, HTTPException


class TunkinRepository:
    def __init__(self):
        self.file: UploadFile = None
        self._allowed_extension = {'.xls', '.xlsx'}
        self._max_file_siz = 50 * 1024 * 1024  # 50MB

    def read_excel(self, file: UploadFile):
        self.file = file
        self._file_checker()

        return {
            "filename": self.file.filename,
            "file_size": self.file.size,
            "content_type": self.file.content_type
        }

    def _file_checker(self):
        """Validasi file sebelum diproses"""
        if not self.file:
            raise HTTPException(status_code=400, detail="File tidak ditemukan")

        if not self.file.filename:
            raise HTTPException(status_code=400, detail="Nama File tidak valid")

        self._validate_file_extension()

    def _validate_file_extension(self):
        file_extension=self.file.filename.lower().split('.')[-1]
        if file_extension not in self._allowed_extension:
            raise HTTPException(
                status_code=400,
                detail=f"Ekstensi file tidak diizinkan. Hanya ekstensi {', '.join(self._allowed_extension)} yang diperbolehkan."
            )