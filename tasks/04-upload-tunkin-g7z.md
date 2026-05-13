# Task 04 — `upload-tunkin-g7z`

**Title:** Extract `PermissionChecker` so authorization logic is testable without FastAPI
**Priority:** P2
**Type:** AFK
**Blocked by:** `upload-tunkin-c5m` (Task 03)
**Blocks:** none

---

## Tujuan (Goal)

Saat ini `require_role()` di `app/repositories/sys_user.py:199–218` melakukan **terlalu banyak hal** di dalam closure dependency FastAPI:

1. Decode Sqid (atau parse token role).
2. Query tabel `sys_role_menu`.
3. Bangun DataFrame.
4. Cek apakah role memiliki menu_code yang diminta.

Akibatnya: aturan otorisasi **hanya bisa diuji lewat full HTTP request**. Tidak ada cara unit test pure.

Tugas: ekstrak menjadi:

- **`PermissionChecker.allows(role_id, menu_codes) -> bool`** — fungsi pure, tidak menyentuh FastAPI maupun pandas.
- **`MenuLookup`** — interface (abstract) untuk mengambil daftar menu_code yang dimiliki sebuah role. Minimal 2 adapter:
  - **DB-backed**: query `sys_role_menu` lewat `DatabaseHelper`.
  - **In-memory dict**: untuk testing — diberi dict `{role_id: [menu_code, ...]}` saat konstruksi.

Setelah itu `require_role()` menyusut menjadi **3 langkah**:

1. Verifikasi token via `TokenVerifier` (sudah ada dari Task 03).
2. Panggil `PermissionChecker.allows(...)`.
3. Raise `HTTPException(403)` bila `False`.

**End-to-end behavior tidak berubah.** Endpoint terlindungi tetap mengembalikan 401 untuk token invalid dan 403 untuk role yang tidak diizinkan.

---

## Wajib: Rujuk `context7` Sebelum Menulis Kode

Sebelum menulis kode:

1. **FastAPI** — pakai project ID dari task sebelumnya. Tanyakan:
   - "How to chain dependencies in FastAPI so one dependency uses the result of another?"
   - "What is the recommended way to raise 401 vs 403 from a dependency?"
2. **Python `abc` (abstract base class)** — jika ragu cara mendefinisikan interface Python yang baik:
   - `context7.resolve-library-id` dengan query `"python abc module"` (atau cari di docs standar via context7 bila tersedia; bila tidak, dokumentasi resmi Python yang ada di context7).
   - Pertanyaan: "How to define an abstract method that subclasses must implement?"
3. Jangan menebak nama exception/decorator. Cek dulu.

---

## Langkah-Langkah Pengerjaan (Berurutan)

### Langkah 1 — Pelajari `require_role()` saat ini

1. Buka `app/repositories/sys_user.py:199–218`. Baca baris per baris.
2. Catat:
   - Bagaimana role_id diambil dari token.
   - Query SQL yang digunakan ke `sys_role_menu`.
   - Bagaimana DataFrame digunakan (apakah dipakai untuk apa lagi selain cek membership? — sepertinya hanya cek membership; kalau iya, DataFrame bisa diganti dengan `set` Python).
3. Cari semua endpoint yang memanggil `require_role([...])`.

### Langkah 2 — Konsultasi `context7` (wajib)

Jalankan flow context7. Pastikan paham cara FastAPI compose dependency dan cara `abc.ABC` / `Protocol`.

### Langkah 3 — Desain interface `MenuLookup`

1. Buat sebuah class abstract / `Protocol`:
   - Method: `menu_codes_for(role_id: int) -> set[str]`.
2. Letakkan di `app/auth/menu_lookup.py` (atau lokasi yang konsisten dengan struktur Task 03).
3. Konsultasi context7 untuk memutuskan antara `abc.ABC` vs `typing.Protocol` — keduanya OK; pilih satu dan konsisten.

### Langkah 4 — Implementasi adapter DB

1. Buat `DBMenuLookup` yang menerima `DatabaseHelper` (via `Depends` chain).
2. Method `menu_codes_for(role_id)` jalankan query `sys_role_menu` untuk role tersebut, return sebagai `set[str]`.
3. **Tidak perlu pandas** — pakai list/set Python biasa.

### Langkah 5 — Implementasi adapter in-memory

1. Buat `InMemoryMenuLookup` yang menerima `dict[int, set[str]]` di konstruktor.
2. Method `menu_codes_for(role_id)` cukup return value dari dict (atau set kosong bila tidak ada).
3. Dipakai khusus di test — tidak menyentuh DB.

### Langkah 6 — Implementasi `PermissionChecker`

1. Letakkan di `app/auth/permission_checker.py` (atau modul yang konsisten).
2. Konstruktor menerima `MenuLookup`.
3. Method `allows(role_id: int, required_menu_codes: list[str]) -> bool`:
   - Ambil set menu_code role tersebut dari `MenuLookup`.
   - Return `True` bila **semua** required_menu_codes ada di set (atau gunakan aturan yang sama dengan implementasi lama — periksa dulu apakah "any" atau "all" sesuai behavior existing!).
4. **Tidak ada** import FastAPI di file ini.

> Penting: cek logic lama persis — apakah `require_role([...])` saat ini menerapkan "user harus punya **semua** menu_code" atau "**salah satu**"? Ikuti semantik yang sama supaya behavior tidak berubah.

### Langkah 7 — Refactor `require_role()`

1. Sekarang `require_role(menu_codes)` cukup mengembalikan dependency factory.
2. Di dalam dependency:
   - Inject `verifier: TokenVerifier = Depends(...)` dan `permission: PermissionChecker = Depends(...)`.
   - Decode token via `verifier.verify(token)` → ambil `role_id` dari claims.
   - Bila decode gagal → raise `HTTPException(401)`.
   - Panggil `permission.allows(role_id, menu_codes)` → bila `False` raise `HTTPException(403)`.
   - Bila `True`, return user/claims yang dibutuhkan endpoint.
3. Hapus query DB, DataFrame, dan logic Sqids dari dalam `require_role`.

### Langkah 8 — Unit test `PermissionChecker`

1. Buat test file (mis. `tests/test_permission_checker.py`).
2. **Tidak boleh** import FastAPI / `TestClient`.
3. Skenario minimal:
   - Role memiliki menu_code yang diminta → `allows` return `True`.
   - Role tidak memiliki menu_code → `allows` return `False`.
   - Role tidak terdaftar sama sekali (kasus edge) → return `False`.
4. Pakai `InMemoryMenuLookup` untuk seed data.

### Langkah 9 — Integration test auth tetap hijau

1. Jalankan suite integration auth dari Task 03 — semua harus tetap pass.
2. Tambahkan minimal satu integration test untuk endpoint terlindungi (`/me` misalnya) yang mengecek:
   - 200 untuk role yang punya menu_code yang benar.
   - 403 untuk role yang tidak punya.
   - 401 untuk token invalid/missing.

---

## Acceptance Criteria

- [ ] Class `PermissionChecker` ada dan **tidak** meng-import FastAPI.
- [ ] Interface `MenuLookup` punya minimal 2 adapter: DB-backed dan in-memory.
- [ ] `require_role()` adalah komposisi tipis dari `TokenVerifier` + `PermissionChecker` + raise 401/403.
- [ ] Unit test `PermissionChecker` ada dan jalan **tanpa** menjalankan FastAPI.
- [ ] Integration test auth existing tetap pass.

---

## Catatan & Hal yang Harus Dihindari

- Jangan pakai pandas untuk cek membership — pakai `set` Python.
- Jangan membuat `PermissionChecker` punya akses langsung ke `DatabaseHelper` — itulah gunanya `MenuLookup`.
- Jangan menggabungkan logic auth dengan logic role-menu di satu class — pisahnya yang penting.
- Jangan rapat-rapat dengan FastAPI di module `permission_checker.py` — file itu harus bisa dibuka tanpa FastAPI ter-install.
- Tetap konsultasi `context7` saat ragu.
