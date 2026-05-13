# Task 01 — `upload-tunkin-ufj`

**Title:** Wire repositories and helpers through FastAPI `Depends` instead of module-level singletons
**Priority:** P2
**Type:** AFK (Away From Keyboard — safe to do without human review during execution)
**Blocked by:** none
**Blocks:** `upload-tunkin-c5m`, `upload-tunkin-rsp`

---

## Tujuan (Goal)

Saat ini setiap router membuat repository sebagai variabel global di tingkat modul, contohnya `repository = TunkinRepository()` di `app/routers/tunkin.py`, dan `token_helper = TokenHelper()` di `app/repositories/tunkin_repository.py`. Karena instance ini di-share oleh seluruh request, **tidak ada test seam** — kita tidak bisa mengganti dependency dengan fake/mock di test.

Tugas: ganti semua singleton modul tersebut dengan **FastAPI `Depends` factory** sehingga `app.dependency_overrides[...]` bisa digunakan di test.

**End-to-end behavior tidak boleh berubah.** Semua endpoint (`/token`, `/refresh`, `/me`, `/validate`, `GET /tunkin/{periode}`, `POST /tunkin/upload`) harus mengembalikan response yang sama persis seperti sebelumnya.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

Sebelum mulai mengubah kode apa pun yang melibatkan FastAPI (`Depends`, dependency injection, dependency override), **kamu wajib bertanya ke `context7`**:

1. Panggil `context7.resolve-library-id` dengan query `"FastAPI dependency injection Depends pattern"` untuk mendapatkan project ID resmi FastAPI.
2. Panggil `context7.query-docs` dengan ID tersebut dan pertanyaan spesifik, misalnya:
   - "How to define a factory function used with `Depends` for a class-based repository?"
   - "How does `app.dependency_overrides` work for testing?"
   - "Should `Depends` factories return a singleton or a fresh instance per request?"
3. Jawab kebutuhan implementasi **strictly berdasarkan docs yang diambil**. Jangan menebak API FastAPI dari ingatan.

Lakukan langkah ini lagi setiap kali ragu tentang signature, type hint, atau lifecycle suatu dependency.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Inventarisasi semua singleton yang harus dihapus

1. Buka folder `app/routers/` dan `app/repositories/`.
2. Cari semua baris yang membuat instance di level modul (di luar function/class). Yang harus dicatat:
   - `repository = TunkinRepository()` di `app/routers/tunkin.py`
   - `token_helper = TokenHelper()` di `app/repositories/tunkin_repository.py`
   - Cari juga pola serupa di `app/routers/auth.py`, `app/repositories/sys_user.py`, `app/repositories/sys_menu.py`, dan helper lain.
3. Tulis daftarnya (di buku catatan / scratch file kamu, bukan di repo) — daftar ini jadi acuan langkah berikutnya.

### Langkah 2 — Konsultasi `context7` (wajib)

Lakukan flow di bagian "Wajib: Rujuk context7" di atas **sebelum** menulis baris kode pertama. Pastikan kamu paham:

- Bagaimana mendeklarasikan factory `def get_tunkin_repository() -> TunkinRepository:` dan menggunakannya sebagai `Depends(get_tunkin_repository)`.
- Bagaimana FastAPI me-resolve dependency yang juga butuh dependency lain (nested).
- Bagaimana `app.dependency_overrides` bekerja.

### Langkah 3 — Buat factory untuk setiap repository / helper

Untuk setiap item dalam inventaris Langkah 1:

1. Buat sebuah **factory function** (atau provider) yang me-return instance baru. Tempatkan di file yang dekat dengan kelasnya — misalnya factory `TunkinRepository` ada di `app/repositories/tunkin_repository.py`, factory `TokenHelper` ada di file token helper-nya, dst.
2. Nama factory disarankan `get_<nama_repository>`, contoh: `get_tunkin_repository`, `get_token_helper`, `get_sys_user_repository`, dst. Konsisten saja.
3. Jika sebuah repository membutuhkan dependency lain (misalnya akses ke `DatabaseHelper`), factory tersebut **juga** harus memakai `Depends(...)` di parameter-nya — jangan instantiate langsung di dalam factory.

> Catatan: factory **tidak** boleh menyimpan instance di variabel global. Setiap pemanggilan factory membuat instance baru (FastAPI yang men-cache per request kalau memang diperlukan — periksa di context7).

### Langkah 4 — Update router untuk pakai `Depends`

Di setiap router (`app/routers/tunkin.py`, `app/routers/auth.py`, dst.):

1. Hapus baris singleton modul (mis. `repository = TunkinRepository()`).
2. Tambahkan parameter pada handler endpoint: `repository: TunkinRepository = Depends(get_tunkin_repository)`.
3. Gunakan `repository.<method>(...)` seperti sebelumnya.
4. Lakukan hal yang sama untuk helper lain (`TokenHelper`, dll.).

### Langkah 5 — Update repositories yang juga menyimpan singleton

Di `app/repositories/tunkin_repository.py` (dan file repository lain yang sejenis):

1. Hapus baris seperti `token_helper = TokenHelper()` di level modul.
2. Jika method membutuhkannya, terima sebagai parameter atau ambil via dependency tree di router (lebih bersih). Jangan re-instantiate di dalam method.

### Langkah 6 — Smoke test override

Tujuan: membuktikan bahwa test seam sudah hidup.

1. Tulis sebuah **smoke test sederhana** (pakai `pytest` + `TestClient` FastAPI). Tanyakan ke `context7` cara penggunaan `TestClient` dan `app.dependency_overrides` jika belum yakin.
2. Di test tersebut: definisikan fake class (mis. `FakeTunkinRepository`) yang me-return data dummy, lalu lakukan `app.dependency_overrides[get_tunkin_repository] = lambda: FakeTunkinRepository()`, panggil endpoint, dan assert response berisi data dummy tadi.
3. Test ini cukup minimal — yang penting menunjukkan override bekerja.

### Langkah 7 — Verifikasi end-to-end

1. Jalankan aplikasi: `uv run uvicorn app.main:app --reload --port 8000`.
2. Hit setiap endpoint yang terdampak manual atau via `curl`/Postman. Bandingkan dengan response sebelum refactor (boleh pakai response yang sudah pernah tersimpan, atau test di branch lama).
3. Pastikan tidak ada perubahan shape, status code, atau header response.

---

## Acceptance Criteria

Tugas dianggap selesai bila **semua** poin berikut terpenuhi:

- [ ] Tidak ada lagi instantiasi repository atau helper di level modul di seluruh `app/routers/` dan `app/repositories/`.
- [ ] Semua repository dan helper diperoleh melalui `Depends(...)` di handler endpoint.
- [ ] Semua endpoint existing mengembalikan response yang identik dengan sebelumnya (status code, body, header).
- [ ] Ada satu smoke test yang membuktikan `app.dependency_overrides` bisa mengganti sebuah repository tanpa monkey-patch.
- [ ] Tidak ada import circular baru yang muncul.

---

## Catatan & Hal yang Harus Dihindari

- Jangan ubah signature method internal repository di task ini — fokusnya hanya pemindahan ke `Depends`.
- Jangan menambah caching/singleton tersembunyi (misalnya `@lru_cache` pada factory) tanpa konfirmasi ke `context7` apakah itu pola yang tepat untuk dependency stateful.
- Jangan menulis dokumentasi tambahan di repo (mis. README baru) kecuali diminta.
- Jika ada pertanyaan tentang FastAPI yang belum yakin → **balik ke `context7` lagi**. Jangan tebak.
