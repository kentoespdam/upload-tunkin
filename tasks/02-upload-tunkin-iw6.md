# Task 02 — `upload-tunkin-iw6`

**Title:** Move Sqids ID encoding out of `DatabaseHelper.fetch_page` to the HTTP edge; make encoding deterministic
**Priority:** P2
**Type:** **HITL (Human-In-The-Loop)** — on-wire ID format akan berubah. **Wajib dapat konfirmasi human** bahwa tidak ada client eksternal yang bergantung pada format ID lama sebelum di-merge.
**Blocked by:** none (independen dari rantai auth — boleh paralel dengan task 01)
**Blocks:** none

---

## Tujuan (Goal)

Saat ini `DatabaseHelper.fetch_page` (lihat `app/core/databases.py:108`) langsung memanggil `SqidsHelper` untuk meng-encode ID — ini adalah kebocoran concern presentasi ke dalam data layer. Lebih parah: `SqidsHelper.encode()` di `app/core/config.py:44–50` **mencampurkan `datetime.now()`** ke dalam payload, sehingga ID yang sama akan menghasilkan string encoded yang berbeda di setiap pemanggilan. Akibatnya:

- Round-trip encode→decode tidak konsisten.
- Test tidak bisa assert nilai encoded ID karena selalu berubah.

Tugas: pisahkan concern.

1. `DatabaseHelper.fetch_page` harus me-return ID sebagai **integer mentah**.
2. Encoding ID Sqids dipindahkan ke **HTTP edge** — di dalam `ResponseBuilder.page()` (atau modul kecil `IDCodec` yang dipanggil saat serialisasi page).
3. `SqidsHelper.encode([id])` harus **deterministik** — input sama → output sama. Hapus semua noise dari `datetime.now()`.

---

## ⚠️ HITL — Approval Wajib Sebelum Merge

Karena format ID encoded yang dikirim ke client **akan berubah**, sebelum task ini di-merge:

1. Konfirmasi ke pemilik project / lead bahwa **tidak ada konsumen API eksternal** yang menyimpan, membandingkan, atau mem-parse format ID lama.
2. Jika ada, diskusikan strategi migrasi (mungkin perlu transitional period atau notifikasi ke client).
3. Catat hasil konfirmasi di issue `upload-tunkin-iw6` (notes).

Pengerjaan kode boleh jalan paralel, **tapi PR tidak boleh di-merge sampai approval ada**.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

Sebelum menulis atau mengubah kode yang menyentuh library Sqids:

1. Panggil `context7.resolve-library-id` dengan query `"sqids python"` untuk mendapatkan project ID Sqids Python.
2. Panggil `context7.query-docs` dengan ID itu dan pertanyaan, contoh:
   - "How does `Sqids.encode()` work? Is it deterministic given the same input list?"
   - "What is the recommended way to set `alphabet` and `min_length`?"
   - "How to decode a string back to the original integer list?"
3. Pastikan implementasi kamu sesuai docs resmi.

Untuk Pydantic / FastAPI response serialization (mungkin diperlukan saat memindahkan encoding ke `ResponseBuilder`), juga konsultasi `context7` dengan library ID Pydantic / FastAPI bila ragu.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Pahami pemakaian saat ini

1. Buka `app/core/databases.py` cari method `fetch_page` (sekitar baris 108). Identifikasi di mana ID di-encode dan kolom apa yang terkena.
2. Buka `app/core/config.py:44–50` — pahami isi `SqidsHelper.encode`. Catat persis bagian mana yang memakai `datetime.now()` atau campuran data lain.
3. Buka `app/models/response_model.py` cari `ResponseBuilder.page()` (atau method pagination terkait). Pahami struktur response page.
4. Cari semua tempat lain yang memanggil `SqidsHelper.encode` / `decode` di seluruh `app/` — pakai grep pada nama class `SqidsHelper`.

### Langkah 2 — Konsultasi `context7` (wajib)

Jalankan flow context7 di bagian atas. Konfirmasi bahwa `Sqids.encode([n])` deterministik bila parameter `alphabet` dan `min_length` tetap.

### Langkah 3 — Bersihkan `SqidsHelper.encode`

1. Hapus penggunaan `datetime.now()` (atau noise lainnya) di `SqidsHelper.encode`.
2. Method harus menerima satu (atau lebih) integer dan langsung memanggil `Sqids.encode(...)` dari library, lalu return string.
3. Pastikan `decode` juga simetris — tulis dengan menengok docs context7.
4. Pastikan parameter `alphabet` dan `min_length` di-load dari config (env) sekali saja di konstruksi, bukan dari `datetime`.

### Langkah 4 — Bersihkan `DatabaseHelper.fetch_page`

1. Hapus semua import `SqidsHelper` dari `app/core/databases.py`.
2. Hapus bagian yang meng-encode kolom ID. ID yang dikembalikan **harus integer mentah**.
3. Pastikan struktur return method tidak berubah selain isi field ID.

### Langkah 5 — Pindahkan encoding ke HTTP edge

Pilih salah satu pendekatan (diskusikan via context7 mana yang ergonomis di FastAPI/Pydantic):

**Opsi A — Inline di `ResponseBuilder.page()`:**
- Di method `page` yang menyusun response paginated, lakukan iterasi atas item, panggil `SqidsHelper.encode([item.id])`, set hasilnya ke field yang akan dikirim ke client.

**Opsi B — Modul `IDCodec` kecil:**
- Buat class kecil `IDCodec` (atau function `encode_id(int) -> str`) di lokasi presentasi (mis. `app/models/`).
- Panggil `IDCodec.encode` di dalam `ResponseBuilder.page()` saat mapping row → response item.

Pilih yang paling sederhana. Yang penting: **lapisan data layer tidak tahu apa-apa tentang Sqids**.

### Langkah 6 — Update semua callers (kalau ada)

Jika ada router/endpoint lain yang mengandalkan ID sudah terencode dari `fetch_page`, sesuaikan: encoding sekarang terjadi di response building, bukan di data fetch.

### Langkah 7 — Unit test round-trip

1. Tulis test yang mem-`encode` sebuah list `[123]` dua kali — assert hasilnya **identik**.
2. Tulis test yang mem-`encode` lalu `decode` — assert nilai yang didapat = nilai awal.
3. Konsultasikan ke `context7` cara minimal menjalankan `pytest` di project ini bila belum ada framework test (lihat README/CLAUDE.md menyebut belum ada test framework — kamu boleh menambahkan `pytest` ke dependency dev kalau perlu, tetapi konfirmasi dulu).

### Langkah 8 — Integration test `GET /tunkin/{periode}`

1. Hit endpoint dan periksa response.
2. ID dalam response harus **string Sqids deterministik** (sama setiap dipanggil), bukan integer mentah.
3. Bentuk field/struktur lain harus tidak berubah.

---

## Acceptance Criteria

- [ ] `DatabaseHelper.fetch_page` mengembalikan ID sebagai integer biasa.
- [ ] Encoding ID hanya terjadi di layer response (ResponseBuilder atau IDCodec).
- [ ] `SqidsHelper.encode` murni (input sama → output sama). Tidak ada `datetime.now()` atau noise lain.
- [ ] `GET /tunkin/{periode}` masih memuat ID terenkode, dalam format deterministik baru.
- [ ] Ada unit test yang membuktikan `encode(decode(x)) == x` dan `encode(x) == encode(x)`.
- [ ] **HITL approval tercatat di issue notes sebelum merge.**

---

## Catatan & Hal yang Harus Dihindari

- Jangan menyentuh chain auth/refactor lain (task 01, 03, 04, 05, 06) — task ini independen.
- Jangan menambah parameter "timestamp" / "salt" baru ke `encode` untuk mencoba "meniru" perilaku lama — sifat non-determinism justru bug yang kita perbaiki.
- Jangan menebak API `sqids`. **Selalu konsultasi context7.**
- Jangan merge tanpa HITL approval — meskipun semua test hijau.
