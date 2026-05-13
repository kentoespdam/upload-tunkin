# Task 06 — `upload-tunkin-5i3`

**Title:** Consolidate `HTTPException` → `ResponseBuilder` mapping into a single registry
**Priority:** P3
**Type:** AFK
**Blocked by:** none (secara teknis), tapi **lebih bersih dikerjakan setelah Task 04** karena auth error adalah konsumen utamanya.
**Blocks:** none

---

## Tujuan (Goal)

Saat ini mapping antara HTTP status code dan method `ResponseBuilder` **terduplikasi di dua tempat**:

1. `app/main.py:19–43` — global exception handler (`if/elif` panjang).
2. `app/models/response_model.py:379–394` — `ResponseBuilder.from_http_exception` (`if/elif` panjang yang sama).

Akibat: menambah satu error class baru = harus edit **dua tabel**. Cepat sekali drift.

Tugas: gabungkan menjadi **satu registry tunggal** di `ResponseBuilder`. Setelahnya:

- Global exception handler menjadi **one-liner** yang memanggil registry.
- `ResponseBuilder.from_http_exception` menggunakan registry yang sama.

**End-to-end behavior tidak berubah.** `HTTPException` dengan status 400/401/403/404/422/500 (dan apa pun yang sudah di-handle sekarang) harus menghasilkan response yang **shape**, **status code**, dan **body**-nya identik.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

1. **FastAPI** — pakai project ID dari task sebelumnya.
   - Pertanyaan: "How to register a custom exception handler for `HTTPException` globally?"
   - "What is the recommended signature for an exception handler in FastAPI?"
2. **Python pattern matching / dict dispatch** — bila ragu cara mendesain registry dict yang clean:
   - Sederhana saja: `dict[int, Callable]`. Tapi kalau ingin pakai `match/case`, periksa idiom di docs Python via context7.

Selalu konfirmasi signature handler FastAPI dan tipe response yang diharapkan.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Pelajari kedua mapping saat ini

1. Buka `app/main.py` baris 19–43. Catat seluruh tabel mapping (status code → method `ResponseBuilder`).
2. Buka `app/models/response_model.py` baris 379–394. Catat tabel mapping kedua.
3. Bandingkan keduanya:
   - Apakah daftar status code-nya sama?
   - Apakah method `ResponseBuilder` yang dipanggil sama untuk setiap status?
   - Apakah ada cabang khusus (misalnya body custom untuk 422)?
4. **Catat perbedaan apa pun** — bila ada perbedaan, klarifikasi mana yang benar (kemungkinan besar perlu cocokkan ke salah satu, tapi minta konfirmasi ke pemilik project bila ragu).

### Langkah 2 — Konsultasi `context7` (wajib)

Jalankan flow context7 untuk handler FastAPI.

### Langkah 3 — Desain registry

1. Lokasi: dalam `ResponseBuilder` (di `app/models/response_model.py`).
2. Bentuk: `dict[int, Callable[..., Response]]` atau method-method bound di class. Sederhananya:
   ```text
   _STATUS_TO_BUILDER = {
       400: ResponseBuilder.bad_request,
       401: ResponseBuilder.unauthorized,
       403: ResponseBuilder.forbidden,
       404: ResponseBuilder.not_found,
       422: ResponseBuilder.unprocessable,
       500: ResponseBuilder.server_error,
       # tambahkan sesuai mapping yang teridentifikasi di Langkah 1
   }
   ```
   (nama method `ResponseBuilder` ikuti yang sudah ada — jangan rename di task ini.)
3. Sediakan **default fallback** untuk status code yang tidak terdaftar. Default existing biasanya `server_error` atau equivalent — periksa di Langkah 1.

### Langkah 4 — Method dispatch tunggal

1. Di `ResponseBuilder`, buat satu method `from_http_exception(exc: HTTPException) -> Response`:
   - Ambil `status_code` dari `exc`.
   - Lookup di registry. Bila tidak ada, pakai fallback.
   - Panggil method tersebut dengan argumen yang konsisten (message dari `exc.detail`, dst.).
2. Method ini menggantikan kedua if/elif chain.

### Langkah 5 — Update global exception handler di `main.py`

1. Handler `HTTPException` di `main.py` menjadi:
   - Terima `request` dan `exc`.
   - Return `ResponseBuilder.from_http_exception(exc)`.
2. Pastikan signature handler **sesuai dokumentasi FastAPI** (context7). Pastikan tipe return-nya `Response` atau `JSONResponse` yang valid.

### Langkah 6 — Bersihkan `response_model.py`

1. Hapus if/elif chain lama di `from_http_exception` — sudah digantikan oleh registry dispatch.
2. Pastikan tidak ada duplikasi.

### Langkah 7 — Test

1. **Unit test registry**:
   - Untuk setiap status code yang terdaftar, panggil `ResponseBuilder.from_http_exception(HTTPException(status_code=...))` dan assert response shape, status code, body.
   - Untuk status code yang tidak terdaftar, assert bahwa fallback method-nya dipakai.
2. **Integration test**:
   - Tambahkan endpoint sementara (atau pakai yang sudah ada) yang me-raise `HTTPException` dengan masing-masing status code yang terdaftar. Pakai `TestClient` (lihat context7). Bandingkan body response sebelum dan sesudah refactor — **harus identik byte-by-byte** (atau setidaknya struktur JSON yang sama).
3. Bila tersedia, jalankan kembali integration test auth (Task 03/04) dan upload (Task 05) — pastikan tidak ada regresi.

---

## Acceptance Criteria

- [ ] Hanya ada **satu registry/dispatch table** yang memetakan status code → method `ResponseBuilder`.
- [ ] Handler `HTTPException` di `main.py` adalah pemanggilan tipis ke `ResponseBuilder` (efektif one-liner).
- [ ] `ResponseBuilder.from_http_exception` memakai registry yang sama.
- [ ] Test mencakup **semua status code yang saat ini di-handle** dan assert response payload identik dengan sebelum refactor.
- [ ] Tidak ada lagi if/elif chain duplikat untuk mapping ini.

---

## Catatan & Hal yang Harus Dihindari

- Jangan rename method `ResponseBuilder` yang sudah ada di task ini — fokus hanya pada konsolidasi.
- Jangan ganti shape JSON response — kontrak harus dipertahankan.
- Bila ada perbedaan antara kedua mapping lama, **konfirmasi dulu** mana yang benar sebelum menyatukan; jangan asal pilih satu.
- Jangan menambah handler untuk exception **non**-`HTTPException` di task ini — itu di luar scope.
- Selalu konsultasi `context7` saat ragu tentang FastAPI exception handler.
