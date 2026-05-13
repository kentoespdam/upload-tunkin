# Urutan Pengerjaan: Refactor ke Domain-Module Layout (+ CQRS Tunkin Upload)

Lima issue saling berurutan — kerjakan dari atas ke bawah. Setiap issue **wajib** lewat fase research `context7` sebelum menulis kode. Tidak boleh ada potongan kode di issue maupun di sini; semua dijelaskan dalam high-level language.

> Konteks arsitektur: codebase saat ini disusun by-layer (`routers/`, `services/`, `repositories/`). Penambahan endpoint Organization sebagai domain ketiga memvalidasi pindah ke domain-module layout sesuai FastAPI best practices (Zhanymkanov). `response_model.py` (434 baris) dipecah lebih dulu jadi fondasi import untuk semua domain. `UploadKpiCommand` memperkenalkan seam CQRS untuk write-path Tunkin supaya pipeline upload bisa dipanggil dari non-HTTP entrypoint (CLI/worker). Read-path tetap router→repository langsung (rule: handler hanya jika ada orchestration >1 step).
>
> Referensi keputusan:
> - `CONTEXT.md` — kosakata domain (Periode `YYYYMM`, NIPAM, KPI Record, KPI Upload, Tunkin Page, Organization)
> - `docs/adr/0001-tunkin-owns-organization-join.md` — Tunkin tetap memegang JOIN ke `organization`; dua repo membaca tabel yang sama adalah konsekuensi sadar

---

## 1. `upload-tunkin-7m9` — Split `response_model.py` (434 lines) into `responses/` package

- [ ] Klaim issue: `bd update upload-tunkin-7m9 --claim`
- [ ] Baca `app/models/response_model.py` end-to-end, kelompokkan isinya jadi tiga bucket: **schemas** (BaseResponse, BasePageResponse, Token, BaseToken, User, RefreshTokenRequest), **success builders** (success, ok, created, paginated, dst.), **error mapping** (bad_request, unauthorized, forbidden, not_found, conflict, internal_server_error, registry `from_http_exception` & `from_exception`)
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **pola memisahkan response schemas dari response builders**, dan penggunaan `JSONResponse` di luar handler
- [ ] Buat package `app/responses/` dengan tiga file: `schemas.py`, `builder.py`, `errors.py`. Masing-masing target di bawah 200 baris
- [ ] Pindahkan tipe Pydantic ke `schemas.py` (tanpa `JSONResponse`/`uuid`/`HTTPException` import — jaga supaya importable oleh service/command layer)
- [ ] Pindahkan method success ke `builder.py`; pertahankan API publik (`success`, `ok`, `paginated`, dll.) supaya call-site router tidak berubah signature-nya
- [ ] Pindahkan error registry + `from_exception`/`from_http_exception` ke `errors.py`
- [ ] Tinggalkan shim ringan di `app/models/response_model.py` yang re-export simbol publik supaya router lama belum perlu di-update (akan dibersihkan di issue #3 & #4)
- [ ] Uji manual: panggil satu endpoint sukses + satu yang melempar error — payload, status code, dan header request_id identik dengan sebelumnya
- [ ] `bd close upload-tunkin-7m9`

---

## 2. `upload-tunkin-yuo` — Create `app/organization/` domain module dengan `GET /organization`

> Blocked sampai #1 selesai (perlu `app/responses/` baru).

- [ ] Klaim issue: `bd update upload-tunkin-yuo --claim`
- [ ] Konfirmasi role: endpoint **public** (tanpa `require_role`), berperan sebagai filter di FE halaman Tunkin
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **domain-based project structure** (Zhanymkanov), inline dependency factory, dan pola `APIRouter` per domain
- [ ] Inspeksi struktur tabel `organization` (lewat repository lama atau skema DB) — tentukan kolom yang ditampilkan ke FE (id, nama; cek apakah perlu kode/parent)
- [ ] Buat layout `app/organization/`: `router.py` (definisi `GET /organization`), `repository.py` (`OrganizationRepository.list(...)` + factory `get_organization_repository()` inline di file yang sama), `schemas.py` (`Organization`, opsional `OrganizationFilter` kalau ada query param)
- [ ] Repository **tidak** memakai JOIN — SELECT mandiri terhadap tabel `organization` (ADR-0001 menjelaskan kenapa Tunkin tetap punya JOIN-nya sendiri)
- [ ] ID di-encode lewat `SqidsHelper` sebelum keluar response (konsisten dengan pola Tunkin Page)
- [ ] Daftarkan router di `app/main.py`
- [ ] Uji manual: panggil `GET /organization` tanpa Authorization header → 200 dengan list rapi; pastikan tidak menabrak `require_role`
- [ ] `bd close upload-tunkin-yuo`

---

## 3. `upload-tunkin-bki` — Pindahkan auth ke `app/auth/` domain module

> Blocked sampai #1 selesai. Bisa paralel dengan #2 kalau dikerjakan oleh orang berbeda.

- [ ] Klaim issue: `bd update upload-tunkin-bki --claim`
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **domain module imports** dan cara mempertahankan `Depends()` saat memindahkan file (ingat: `require_role` **tetap** di `app/core/security.py` karena cross-cutting)
- [ ] Pindahkan `app/routers/auth.py` → `app/auth/router.py`
- [ ] Pindahkan `app/repositories/sys_user.py` + `app/repositories/sys_menu.py` → `app/auth/repository.py` (gabung kalau muat di bawah 200 baris; pisah kalau perlu)
- [ ] Konsolidasi `app/auth/permission_checker.py` + `app/auth/menu_lookup.py` → `app/auth/permissions.py`
- [ ] `app/core/security.py` **tidak dipindah** (`require_role`, `TokenIssuer`, `TokenVerifier`, `oauth2_scheme` dipakai oleh banyak domain — tetap di core)
- [ ] Buat `app/auth/schemas.py` untuk `RefreshTokenRequest` dan tipe spesifik auth (Token/User boleh tetap di `app/responses/schemas.py` karena dibagi banyak domain — jangan dipindah kalau bikin import cycle)
- [ ] Factory `get_X()` tetap inline di file yang sama dengan class-nya (keputusan grilling: belum perlu `dependencies.py` terpisah)
- [ ] Update import di seluruh codebase (`app/core/security.py` masih perlu import `SysUserRepository` dari lokasi baru)
- [ ] Hapus file lama setelah semua import sudah merujuk lokasi baru
- [ ] Uji manual: `/token`, `/refresh`, `/me`, `/validate` semua hijau; endpoint Tunkin masih lolos `require_role(["payrollprocess"])`
- [ ] `bd close upload-tunkin-bki`

---

## 4. `upload-tunkin-hy8` — Pindahkan tunkin ke `app/tunkin/` + introduce `UploadKpiCommand`

> Blocked sampai #1 selesai. Disarankan setelah #3 supaya import path stabil.

- [ ] Klaim issue: `bd update upload-tunkin-hy8 --claim`
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **CQRS-style command handlers di FastAPI**, plus pola injeksi pipeline (gate → parser → repo) via `Depends`
- [ ] Pindahkan `app/routers/tunkin.py` → `app/tunkin/router.py`
- [ ] Pindahkan `app/repositories/tunkin_repository.py` + `app/repositories/kpi_repository.py` → `app/tunkin/repository.py`
- [ ] Pindahkan `app/services/file_gate.py` + `app/services/kpi_sheet_parser.py` → `app/tunkin/services.py`
- [ ] Pindahkan model request/response spesifik Tunkin (`TunkinRequest`, `KPIRecord`, `UpsertResult`) ke `app/tunkin/schemas.py`
- [ ] Buat `app/tunkin/commands.py` berisi `UploadKpiCommand` — interface: terima `FileGate`, `KPISheetParser`, `KPIRepository` lewat constructor (DI); satu method `execute(file: UploadFile) -> UpsertResult` yang membungkus gate→parse→upsert
- [ ] Factory `get_upload_kpi_command()` inline di `commands.py` — compose tiga dependency via `Depends`
- [ ] Router `POST /upload` menjadi satu baris: terima `UploadKpiCommand` lewat `Depends`, panggil `.execute(file)`, return ke `response_builder.success(...)`
- [ ] Router `GET /{periode}` **tidak** dibungkus command/query handler — list endpoint langsung panggil `TunkinRepository.fetch_page_data` (keputusan grilling: handler hanya jika ada orchestration)
- [ ] `TunkinRepository.fetch_page_data` **tetap memegang JOIN ke `organization`** (ADR-0001) — jangan diganti menjadi pemanggilan `OrganizationRepository`
- [ ] Update import di seluruh codebase; hapus folder lama (`app/routers/`, `app/services/`, `app/repositories/`) setelah Tunkin & Auth sudah pindah
- [ ] Uji manual: `GET /tunkin/{periode}` paginated jalan; `POST /tunkin/upload` dengan file Excel valid → `UpsertResult` benar; file invalid → error tetap sesuai
- [ ] Sentuh `app/cli.py` (opsional, scope check): konfirmasi `UploadKpiCommand` bisa dipanggil tanpa FastAPI — kalau belum, catat issue follow-up
- [ ] `bd close upload-tunkin-hy8`

---

## 5. `upload-tunkin-dot` — Hapus try/except di router, andalkan `@app.exception_handler` di `main.py`

> Blocked sampai #3 **dan** #4 selesai.

- [ ] Klaim issue: `bd update upload-tunkin-dot --claim`
- [ ] Baca ulang `app/main.py` — pastikan `@app.exception_handler(HTTPException)` dan `@app.exception_handler(Exception)` mengembalikan response yang identik dengan yang dihasilkan `response_builder.from_exception(...)` di per-route try/except
- [ ] `context7`: `resolve-library-id "fastapi"` → `query-docs` tentang **exception handler precedence** dan ordering (HTTPException vs generic Exception)
- [ ] Identifikasi bug silent fall-through di `tunkin.upload_file`: cabang `elif status_code == 500` lalu tidak ada `else` → status code lain (403/404/422) saat ini return `None`. Verifikasi handler global menangkapnya dengan benar setelah try/except dihapus
- [ ] Hapus semua try/except dari `app/tunkin/router.py` dan `app/auth/router.py` — endpoint cukup return hasil sukses
- [ ] Pastikan `LOGGER.error(e)` yang sebelumnya di per-route blok dipindah/diduplikasi di global exception handler kalau memang dibutuhkan (jangan hilangkan logging diam-diam)
- [ ] Uji manual matrix: endpoint sukses → 200 normal; HTTPException 400 → payload error sesuai; HTTPException 403 (sebelumnya fall-through!) → sekarang harus 403 dengan payload rapi; exception tak terduga → 500 dengan request_id
- [ ] `bd close upload-tunkin-dot`

---

## Session close

- [ ] `git status` bersih
- [ ] `bd dolt push`
- [ ] `git push`
- [ ] Verifikasi `git status` menampilkan "up to date with origin"
