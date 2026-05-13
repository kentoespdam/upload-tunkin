# Task 03 — `upload-tunkin-c5m`

**Title:** Split `TokenHelper` into `TokenIssuer` and `TokenVerifier`; break cycle with `SysUserRepository`
**Priority:** P2
**Type:** AFK
**Blocked by:** `upload-tunkin-ufj` (Task 01)
**Blocks:** `upload-tunkin-g7z` (Task 04)

---

## Tujuan (Goal)

Saat ini `TokenHelper` melakukan **tiga concern** sekaligus:

1. Menerbitkan JWT (claims → token).
2. Memverifikasi JWT (token → claims, atau raise error).
3. Melakukan lookup user via `SysUserRepository` (sehingga `TokenHelper` meng-import `SysUserRepository`, dan sebaliknya — **circular coupling**).

Selain itu `require_role()` membangun instance baru `TokenHelper` di setiap request.

Tugas: pisahkan menjadi dua modul / class **pure** yang tidak saling tergantung:

- **`TokenIssuer`** — input: claims (data user + role), output: JWT string. Tidak peduli soal user repository.
- **`TokenVerifier`** — input: JWT string, output: claims dict (atau raise jika token invalid). Juga tidak peduli soal user repository.

Lookup user (jika dibutuhkan, misalnya di `/me`) dikomposisikan **di router**, bukan di dalam token classes.

**End-to-end behavior tidak boleh berubah.** Endpoint `/token`, `/refresh`, `/me`, `/validate` harus tetap berfungsi dengan response shape yang sama.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

Sebelum menulis/mengubah kode yang menyentuh JWT atau FastAPI:

1. **PyJWT**:
   - `context7.resolve-library-id` dengan query `"PyJWT python"`.
   - `context7.query-docs` dengan pertanyaan seperti:
     - "How to encode a JWT with HS256 and set expiration?"
     - "How to decode and verify a JWT, and which exceptions are raised on invalid/expired tokens?"
     - "Best practice for separating issuance and verification?"
2. **FastAPI** (untuk integrasi `Depends`):
   - Gunakan kembali project ID yang sudah didapat di Task 01.
   - Tanyakan: "How to compose multiple `Depends` (token verifier + user repository) inside a single endpoint?"

Implementasi WAJIB strictly mengikuti docs context7. Jangan tebak nama fungsi atau exception class.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Pelajari `TokenHelper` saat ini

1. Buka file `TokenHelper` (biasanya di `app/repositories/sys_user.py` atau dekat situ — lakukan grep `class TokenHelper`).
2. Catat:
   - Method apa saja yang ada (mis. `create_access_token`, `create_refresh_token`, `decode_token`, `verify`, dll.).
   - Field/atribut yang dipakai (secret key, algorithm, expire minutes).
   - Tempat di mana `SysUserRepository` di-import / dipanggil.
3. Buka `require_role()` di `app/repositories/sys_user.py:199–218`. Pahami flow-nya saat ini.
4. Cari semua caller `TokenHelper` di seluruh `app/`.

### Langkah 2 — Konsultasi `context7` (wajib)

Jalankan flow context7 di atas. Pastikan kamu paham:

- API resmi PyJWT untuk encode/decode (nama parameter, exception yang dilempar).
- Cara FastAPI menyusun nested `Depends`.

### Langkah 3 — Desain modul baru

Buat dua modul / class:

- `TokenIssuer`
  - State: `secret_key`, `algorithm`, `access_expire_minutes`, `refresh_expire_minutes`.
  - Method: `issue_access(claims) -> str`, `issue_refresh(claims) -> str`.
  - **Tidak ada** import `SysUserRepository` atau modul user.
- `TokenVerifier`
  - State: `secret_key`, `algorithm`.
  - Method: `verify(token) -> claims_dict` (raise exception bila invalid/expired — pakai exception yang spesifik, misalnya yang sudah ada di PyJWT, lihat docs context7).
  - **Tidak ada** import `SysUserRepository`.

Lokasi file disarankan: `app/core/security.py` atau modul `app/auth/` baru. Cukup pilih satu yang konsisten dengan struktur existing.

### Langkah 4 — Bersihkan `SysUserRepository`

1. Hilangkan semua import JWT dari `SysUserRepository`.
2. `SysUserRepository` cukup berkutat di akses database user (find by username, verify password, fetch role, dll.).

### Langkah 5 — Update routers `auth.py`

Untuk masing-masing endpoint:

- `POST /token`
  1. Router menerima `sys_user_repo: SysUserRepository = Depends(...)` dan `issuer: TokenIssuer = Depends(...)`.
  2. Lookup user via `sys_user_repo`, validasi password.
  3. Bila valid, panggil `issuer.issue_access(...)` dan `issuer.issue_refresh(...)`.
  4. Return response sama persis seperti sebelumnya.
- `POST /refresh`
  1. Router menerima `verifier: TokenVerifier` dan `issuer: TokenIssuer` via `Depends`.
  2. Verifikasi refresh token via `verifier.verify(...)`.
  3. Bila valid, terbitkan access token baru via `issuer.issue_access(...)`.
- `GET /me`
  1. Router menerima `verifier`, `sys_user_repo` via `Depends`.
  2. Verifikasi token → ambil claims → lookup user.
- `OPTIONS /validate`
  1. Gunakan `verifier` untuk memvalidasi token.

> Catatan: factory `Depends` untuk `TokenIssuer` dan `TokenVerifier` mengikuti pola dari **Task 01**. Jangan kembalikan singleton modul.

### Langkah 6 — Update `require_role()`

Untuk task ini, cukup ubah `require_role()` agar **tidak lagi membuat `TokenHelper` sendiri**. Gantilah dengan: terima `verifier: TokenVerifier = Depends(...)` dan gunakan untuk decode token. Lookup user/role tetap di tempat lama untuk task ini — **pemisahan PermissionChecker** dilakukan di **Task 04** (`upload-tunkin-g7z`), jangan dikerjakan di sini.

### Langkah 7 — Hapus `TokenHelper`

Setelah semua caller pindah ke `TokenIssuer`/`TokenVerifier`, hapus class `TokenHelper` lama. Pastikan tidak ada import yang tertinggal.

### Langkah 8 — Test

1. **Unit test `TokenVerifier`**:
   - Pastikan token valid → return claims.
   - Pastikan token expired → raise exception spesifik.
   - Pastikan token signature tidak cocok → raise exception.
   - **Tidak boleh** ada import FastAPI di test file ini.
2. **Integration test auth**:
   - Login via `/token` → dapat access + refresh token.
   - Refresh via `/refresh` → dapat access token baru.
   - Akses `/me` dengan access token → dapat profile.
   - Akses `/validate` dengan access token → 200/ok shape sama.
   - Untuk integration test, gunakan `TestClient` (lihat context7).

### Langkah 9 — Verifikasi manual

Jalankan aplikasi, hit endpoint dengan curl/Postman. Bandingkan response shape (key, status code) dengan sebelum refactor.

---

## Acceptance Criteria

- [ ] `TokenIssuer` dan `TokenVerifier` adalah class/modul terpisah dan **tidak menyentuh** `SysUserRepository`.
- [ ] `SysUserRepository` tidak lagi mengandung import JWT (pyjwt).
- [ ] Empat endpoint auth (`/token`, `/refresh`, `/me`, `/validate`) lulus integration test end-to-end (mint → refresh → validate).
- [ ] `TokenVerifier` memiliki unit test yang **tidak meng-import FastAPI**.
- [ ] `TokenHelper` lama sudah dihapus dan tidak ada referensinya.

---

## Catatan & Hal yang Harus Dihindari

- Jangan menggabungkan task ini dengan ekstraksi `PermissionChecker` — itu untuk Task 04.
- Jangan membuat issuer + verifier menjadi satu class lagi "untuk kerapian" — pemisahan adalah goal-nya.
- Jangan import `SysUserRepository` di file token. Kalau merasa "harus", berarti komposisi salah — pikirkan ulang di router.
- Selalu rujuk `context7` saat ragu tentang PyJWT atau FastAPI Depends.
