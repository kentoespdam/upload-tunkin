"""Unit tests for FileGate — no FastAPI/DB dependency.

Run: uv run python test_file_gate.py
"""
import io

from app.services.file_gate import FileGate

# Minimal UploadFile stand-in so we don't need FastAPI
class FakeUploadFile:
    def __init__(self, filename, content_type, content=b""):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self):
        return self._content


def test_allowed_extension_passes():
    fg = FileGate()
    import asyncio
    uf = FakeUploadFile("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"some content")
    data = asyncio.run(fg.check(uf))
    assert isinstance(data, bytes)


def test_disallowed_extension_raises():
    fg = FileGate()
    import asyncio
    try:
        uf = FakeUploadFile("data.pdf", "application/pdf", b"content")
        asyncio.run(fg.check(uf))
        assert False, "should have raised"
    except Exception as e:
        from fastapi import HTTPException
        assert isinstance(e, HTTPException)
        assert e.status_code == 400
        assert "Ekstensi" in e.detail


def test_bad_mime_raises():
    fg = FileGate()
    import asyncio
    try:
        uf = FakeUploadFile("data.xlsx", "text/plain", b"content")
        asyncio.run(fg.check(uf))
        assert False
    except Exception as e:
        from fastapi import HTTPException
        assert isinstance(e, HTTPException)
        assert "Tipe konten" in e.detail


def test_empty_filename_raises():
    fg = FileGate()
    import asyncio
    try:
        uf = FakeUploadFile("", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"content")
        asyncio.run(fg.check(uf))
        assert False
    except Exception as e:
        from fastapi import HTTPException
        assert isinstance(e, HTTPException)
        assert "Nama File" in e.detail


def test_oversize_file_raises():
    fg = FileGate()
    from app.services.file_gate import MAX_FILE_SIZE
    big = b"x" * (MAX_FILE_SIZE + 1)
    import asyncio
    try:
        uf = FakeUploadFile("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", big)
        asyncio.run(fg.check(uf))
        assert False
    except Exception as e:
        from fastapi import HTTPException
        assert isinstance(e, HTTPException)
        assert "Ukuran file" in e.detail


def test_zero_size_raises():
    fg = FileGate()
    import asyncio
    try:
        uf = FakeUploadFile("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"")
        asyncio.run(fg.check(uf))
        assert False
    except Exception as e:
        from fastapi import HTTPException
        assert isinstance(e, HTTPException)
        assert "File Kosong" in e.detail


if __name__ == "__main__":
    tests = [test_allowed_extension_passes, test_disallowed_extension_raises,
             test_bad_mime_raises, test_empty_filename_raises,
             test_oversize_file_raises, test_zero_size_raises]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("\nAll FileGate unit tests passed!")
