# Task 05 — `upload-tunkin-rsp`

**Title:** Split Excel upload monolith into `FileGate`, `KPISheetParser`, and `KPIRepository.upsert_batch`
**Priority:** P2
**Type:** AFK
**Blocked by:** `upload-tunkin-ufj` (Task 01)
**Blocks:** none
**Catatan:** Boleh dikerjakan paralel dengan Task 03 dan 04 (jalur auth).

---

## Tujuan (Goal)

`TunkinRepository.upload()` di `app/repositories/tunkin_repository.py:66–172` saat ini **menggabungkan empat concern** dalam satu method:

1. Validasi file (ekstensi, ukuran, MIME).
2. Parsing Excel via pandas.
3. Validasi shape baris (kolom wajib ada, tipe data, dll.).
4. Bulk upsert ke database.

Tidak ada satu pun yang bisa di-unit-test tanpa Excel asli + DB hidup.

Tugas: pecah menjadi tiga modul dengan interface sempit:

- **`FileGate.check(upload_file) -> bytes`** — menerima `UploadFile`, validasi ekstensi/MIME/size, return `bytes` mentah. Raise exception domain bila gagal.
- **`KPISheetParser.parse(bytes, column_spec) -> list[KPIRecord]`** — terima bytes, parse Excel, validasi shape baris, return list dataclass/Pydantic `KPIRecord`.
- **`KPIRepository.upsert_batch(records) -> result`** — terima list `KPIRecord`, lakukan upsert ke DB, return ringkasan hasil.

Router `POST /tunkin/upload` menjadi orchestrator tipis: panggil tiga modul secara berurutan.

**End-to-end behavior tidak berubah.** Semua HTTP response error existing (ekstensi salah, MIME salah, ukuran lebih besar dari limit, kolom hilang, dll.) harus mengembalikan **status code dan body yang identik** dengan sebelumnya.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

Sebelum menyentuh bagian terkait:

1. **FastAPI `UploadFile`**:
   - Pakai project ID FastAPI yang sudah didapat.
   - Pertanyaan: "How to read bytes from `UploadFile`? Is it async? How to check content-type and filename safely?"
2. **Pandas / OpenPyXL** untuk parsing Excel:
   - `context7.resolve-library-id` query `"pandas python"` dan `"openpyxl python"`.
   - Pertanyaan: "How to read an Excel file from bytes (not a path)?", "How to specify sheet, header row, and column dtypes?", "What exceptions are raised when the file is malformed?"
3. **Pydantic** untuk model `KPIRecord` (bila dipakai):
   - `context7.resolve-library-id` query `"pydantic v2"`.
   - Pertanyaan: "How to define a model with strict types and raise on validation failure?"

Jangan tebak signature `pd.read_excel`, `UploadFile.read`, dll. Konsultasi dulu.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Pelajari `upload()` saat ini

1. Buka `app/repositories/tunkin_repository.py:66–172`. Baca per blok.
2. Catat:
   - Daftar ekstensi yang diizinkan.
   - Daftar MIME type yang diizinkan.
   - Batas ukuran file.
   - Nama sheet yang dipakai, header row, daftar kolom wajib.
   - Aturan validasi tiap kolom (mis. nominal harus angka, periode harus 6-digit, dll.).
   - Query upsert ke DB (apakah pakai `INSERT ... ON DUPLICATE KEY UPDATE`, atau lain).
   - HTTP error response yang dilempar di setiap titik (status code + payload). **Ini penting** — harus dipertahankan.
3. Buka `app/routers/tunkin.py` untuk lihat endpoint `POST /upload` saat ini.

### Langkah 2 — Konsultasi `context7` (wajib)

Jalankan flow context7. Konfirmasi cara baca bytes dari `UploadFile` (apakah `await file.read()` mengembalikan `bytes`), cara baca Excel dari BytesIO, dll.

### Langkah 3 — Desain `KPIRecord`

1. Definisikan dataclass / Pydantic model `KPIRecord` dengan field sesuai struktur baris Excel (mis. `periode`, `nipam`, `nominal`, ...). Lihat kolom asli di langkah 1.
2. Letakkan di `app/models/kpi.py` atau modul serupa.

### Langkah 4 — Implementasi `FileGate`

1. Lokasi: `app/services/file_gate.py` (atau modul services baru).
2. Method `check(upload_file: UploadFile) -> bytes`:
   - Periksa ekstensi nama file.
   - Periksa MIME / `content_type`.
   - Baca bytes (sesuai cara dari context7), periksa ukuran.
   - Raise exception domain (bukan langsung `HTTPException`) yang nantinya dipetakan ke HTTP error di router. Bisa class kecil seperti `InvalidExtension`, `InvalidMime`, `FileTooLarge`. Atau, untuk meminimalkan perubahan response, raise `HTTPException` dengan status code + detail persis sama dengan sebelumnya (pragmatis).
3. **Jangan** menyentuh pandas atau DB di sini.
4. Maksimum **~40 LOC per method**.

### Langkah 5 — Implementasi `KPISheetParser`

1. Lokasi: `app/services/kpi_sheet_parser.py`.
2. Method `parse(data: bytes, column_spec) -> list[KPIRecord]`:
   - Bungkus `data` ke `BytesIO`.
   - Panggil `pd.read_excel` atau `openpyxl` (sesuai context7) dengan sheet name + header sesuai existing.
   - Validasi nama kolom — bila ada yang hilang, raise error domain `MissingColumns(...)` (atau equivalent `HTTPException`).
   - Iterasi baris, build `KPIRecord` per baris. Validasi tipe data (jangan biarkan NaN diam-diam masuk).
   - Return list `KPIRecord`.
3. **Jangan** sentuh DB atau FastAPI di sini.
4. Maksimum **~40 LOC per method**. Bila terlalu panjang, pisahkan jadi helper kecil di file yang sama.

### Langkah 6 — Implementasi `KPIRepository.upsert_batch`

1. Lokasi: `app/repositories/kpi_repository.py` (rename atau tambah class baru — jangan campur dengan `TunkinRepository` lama).
2. Konstruktor menerima `DatabaseHelper` via `Depends` (lihat pola Task 01).
3. Method `upsert_batch(records: list[KPIRecord]) -> UpsertResult`:
   - Bangun parameterized query (gunakan `%s` sesuai pola existing).
   - Panggil method bulk save di `DatabaseHelper`.
   - Return ringkasan: jumlah insert, jumlah update, dll. (mirror existing return shape kalau ada).
4. **Jangan** validasi shape baris di sini — itu sudah job parser.
5. Maksimum ~40 LOC per method.

### Langkah 7 — Router orchestration

1. Di `app/routers/tunkin.py`, endpoint `POST /upload`:
   - Inject `file_gate: FileGate = Depends(...)`, `parser: KPISheetParser = Depends(...)`, `kpi_repo: KPIRepository = Depends(...)`.
   - Step 1: `data = await file_gate.check(upload_file)` (atau sync, tergantung context7 panduan UploadFile).
   - Step 2: `records = parser.parse(data, column_spec)`.
   - Step 3: `result = kpi_repo.upsert_batch(records)`.
   - Bungkus result via `ResponseBuilder.ok(...)` seperti sebelumnya.
2. Pastikan exception domain dari setiap step di-map ke `HTTPException` yang **sama persis** dengan format error sebelum refactor (status code, body).

### Langkah 8 — Hapus method `upload()` lama

Setelah orchestrator router pakai modul baru, hapus method lama di `TunkinRepository.upload()`. Pastikan tidak ada caller tersisa.

### Langkah 9 — Unit test (3 modul)

1. **FileGate** — test minimal:
   - Ekstensi salah → raise.
   - MIME salah → raise.
   - File terlalu besar → raise.
   - File valid → return bytes.
   - **Tidak boleh** import MySQL atau FastAPI app langsung. Boleh mock `UploadFile` sederhana.
2. **KPISheetParser** — test minimal:
   - Kolom hilang → raise.
   - File rusak (bytes asal) → raise.
   - File valid (sediakan fixture Excel kecil, atau buat in-memory via openpyxl) → return list `KPIRecord` dengan nilai yang diharapkan.
   - **Tidak boleh** import MySQL atau FastAPI.
3. **KPIRepository** — test minimal:
   - Beri list 2–3 record, mock `DatabaseHelper.save_update`, assert query yang dipanggil & parameter-nya benar.
   - **Tidak boleh** import FastAPI.

### Langkah 10 — Integration test `POST /tunkin/upload`

1. Golden path: kirim file Excel valid → 200 + response shape sama dengan sebelum refactor.
2. Setiap skenario error existing (ekstensi salah, MIME salah, oversize, kolom hilang) → status code + body identik.

---

## Acceptance Criteria

- [ ] `FileGate`, `KPISheetParser`, `KPIRepository` adalah modul terpisah.
- [ ] Masing-masing punya unit test yang **tidak menyentuh FastAPI maupun MySQL**.
- [ ] Integration test `POST /tunkin/upload` lulus untuk file golden path.
- [ ] Semua error existing (ekstensi salah, MIME salah, oversize, kolom hilang) menghasilkan **HTTP response yang identik** dengan sebelum refactor.
- [ ] Tidak ada method di modul baru yang melebihi ~40 LOC.
- [ ] Method `TunkinRepository.upload()` lama sudah dihapus.

---

## Catatan & Hal yang Harus Dihindari

- Jangan bikin "super class" yang menggabungkan ketiga modul kembali — pemisahannya adalah goal.
- Jangan ubah skema DB / nama kolom — hanya refactor kode.
- Jangan biarkan DataFrame "bocor" keluar dari `KPISheetParser` — output harus list dataclass/Pydantic, bukan DataFrame.
- Jangan menebak signature pandas / openpyxl / `UploadFile`. **Selalu konsultasi context7.**
- Jangan ubah format JSON response error — itulah kontrak yang harus dipertahankan.
