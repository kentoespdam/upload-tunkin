# Urutan Pengerjaan: Refactor `app/main.py`

Tiga issue saling berurutan — kerjakan dari atas ke bawah. Setiap issue **wajib** lewat fase research `context7` sebelum menulis kode. Tidak boleh ada potongan kode di issue maupun di sini; semua dijelaskan dalam high-level language.

> Konteks arsitektur: `app/main.py` saat ini memiliki tiga keluhan — IDE warning di `CORSMiddleware`, tiga exception handler bernama sama dengan parameter `request` tak terpakai, dan `ResponseBuilder()` di-instansiasi inline di setiap handler. Tiga issue di bawah memperdalam masing-masing seam tersebut.

---

## 1. `upload-tunkin-ly5` — Refactor CORS middleware setup

- [ ] Klaim issue: `bd update upload-tunkin-ly5 --claim`
- [ ] Baca `app/core/config.py` untuk memahami pola field berbasis env yang sudah ada
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **CORSMiddleware parameters** dan interaksi `allow_origins=['*']` dengan `allow_credentials=True`
- [ ] Tambah field CORS pada `Config` (origins, methods, headers, allow_credentials) dengan default aman untuk dev
- [ ] Buat helper `configure_cors(app, config)` di modul yang sesuai (mis. `app/core/`); seluruh kwargs `CORSMiddleware` di-pass eksplisit di sini
- [ ] Ganti blok `add_middleware(...)` di `main.py` menjadi satu panggilan helper
- [ ] Update `.env.example` (jika ada) dengan variabel baru
- [ ] Jalankan dev server, verifikasi tidak ada IDE warning lagi dan request lintas-origin tetap jalan
- [ ] `bd close upload-tunkin-ly5`

---

## 2. `upload-tunkin-5b9` — Collapse duplicate JWT exception handlers

> Blocked sampai #1 selesai.

- [ ] Klaim issue: `bd update upload-tunkin-5b9 --claim`
- [ ] `context7`: `resolve-library-id "pyjwt"` → `query-docs` tentang **exception hierarchy** (`PyJWTError`, `ExpiredSignatureError`, `InvalidTokenError`, `DecodeError`)
- [ ] Hapus tiga handler bernama sama; ganti dengan satu handler unik untuk `PyJWTError`
- [ ] Branch pesan user-facing dengan `isinstance` (expired vs invalid) — panggilan `response_builder.unauthorized` tetap satu titik
- [ ] Pertahankan header `WWW-Authenticate: Bearer`
- [ ] Rename `request` → `_request` di handler `http_exception_handler` agar warning hilang
- [ ] Uji manual: panggil `/me` tanpa token, dengan token kedaluwarsa, dan dengan token sampah — pastikan status code & pesan sesuai
- [ ] `bd close upload-tunkin-5b9`

---

## 3. `upload-tunkin-j0u` — Normalize `ResponseBuilder` usage

> Blocked sampai #2 selesai.

- [ ] Klaim issue: `bd update upload-tunkin-j0u --claim`
- [ ] Baca ulang `app/models/response_model.py`, konfirmasi `from_http_exception` & `from_exception` tidak butuh state instance
- [ ] `context7` (opsional): `resolve-library-id "fastapi"` → `query-docs` apakah `Depends` bisa di exception handler (jawab: tidak)
- [ ] Promosikan `from_http_exception` & `from_exception` jadi `@classmethod` agar keduanya bisa dipanggil statis maupun via instance
- [ ] Hapus pola `res = ResponseBuilder()` di `main.py`; panggil method statis
- [ ] Pastikan router (`auth.py`, `tunkin.py`) tetap jalan tanpa perubahan (instance dari `Depends` tetap valid)
- [ ] Uji satu endpoint sukses + satu endpoint error per kategori — payload & header identik dengan sebelumnya
- [ ] `bd close upload-tunkin-j0u`

---

## Session close

- [ ] `git status` bersih
- [ ] `bd dolt push`
- [ ] `git push`
- [ ] Verifikasi `git status` menampilkan "up to date with origin"
