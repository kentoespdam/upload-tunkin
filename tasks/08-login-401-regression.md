# Urutan Pengerjaan: Login 401 Regression Post-Refactor

> Setelah commit `1253876` (refactor `main.py`: ly5 + 5b9 + j0u), login via Swagger UI gagal **401 Unauthorized**. Issue ini menginvestigasi penyebab dan memperbaikinya **tanpa membatalkan** tiga refactor sebelumnya. Tidak boleh ada potongan kode di sini; semua high-level. Wajib `context7` sebelum menulis kode.

---

## `upload-tunkin-7er` — Investigate & fix 401 regression at `/token`

- [ ] Klaim issue: `bd update upload-tunkin-7er --claim`
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang:
    - **CORSMiddleware** dengan request kredensial (preflight untuk `POST application/x-www-form-urlencoded`)
    - **OAuth2PasswordRequestForm** (content-type, form fields wajib)
    - **exception_handler** signature & return type
- [ ] Reproduksi:
    - Jalankan dev server (`uv run uvicorn app.main:app --reload --port 8000`)
    - Buka `http://localhost:8000/docs`, klik **Authorize**, isi credential yang sebelum refactor valid
    - Capture status code, body, headers, dan tab **Network** browser (perhatikan preflight `OPTIONS`)
    - Banding silang dengan `curl` langsung ke `POST /token` (content-type `application/x-www-form-urlencoded`)
- [ ] Diagnosis berdasarkan hasil banding silang:
    - **curl OK & Swagger gagal** → preflight CORS. Periksa `Config.cors_allow_methods` & `cors_allow_headers` yang saat ini dimuat sebagai string `'*'` (bukan list). Perbaiki parsing env supaya selalu list, tanpa mengembalikan blok `add_middleware` lama
    - **curl & Swagger sama-sama 401** → cek log `logs/app.log` untuk pesan eksak (`Incorrect username or password` vs lain). Telusuri ke `SysUserRepository.authenticate` / `validate_password`
    - **500 di salah satu** → cek pemanggilan `ResponseBuilder.from_http_exception` di `app/routers/auth.py` setelah promosi `@classmethod`
- [ ] Terapkan fix minimal sesuai diagnosis
- [ ] Verifikasi:
    - `POST /token` via **Swagger UI** mengembalikan 201 dengan `access_token` + `refresh_token`
    - `POST /token` via **curl** identik
    - `/me` dengan token valid sukses 200
    - `/me` dengan token kedaluwarsa → 401 dengan pesan benar (regressi 5b9 tidak kembali)
- [ ] Pastikan tidak mengembalikan:
    - IDE warning di `CORSMiddleware` (ly5)
    - Tiga handler PyJWT duplikat (5b9)
    - Pola `ResponseBuilder()` inline di `main.py` (j0u)
- [ ] `bd close upload-tunkin-7er`

---

## Session close

- [ ] `git status` bersih
- [ ] `bd dolt push` (skip jika remote Dolt belum dikonfigurasi)
- [ ] `git push`
- [ ] Verifikasi `git status` menampilkan "up to date with origin"
