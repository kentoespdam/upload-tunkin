# Domain Context — Upload Tunkin

Domain vocabulary used across this codebase. Architectural terms (Module, Seam, Adapter, Depth) live in the `/improve-codebase-architecture` skill — this file is for *what we're modeling*, not *how we structure code*.

## Core terms

**Periode** — payroll period code, formatted as `YYYYMM` (4-digit year + 2-digit month, e.g. `202605`). Path parameter for `GET /tunkin/{periode}`. Treated as an opaque string everywhere — no date arithmetic on it.

**NIPAM** — *Nomor Induk Pegawai* at PDAM (employee ID number). Natural identifier for an employee. Used as filter in `TunkinRequest` and as part of the natural key in `salary_kpi`.

**KPI Record** — one row in the `salary_kpi` table. Carries `periode`, `nipam`, and `nominal`. Uniqueness is `(periode, nipam)`.

**KPI Upload** — the Excel-driven pipeline: file validation → sheet parsing → batch upsert. Triggered by `POST /tunkin/upload`. Idempotent via `ON DUPLICATE KEY UPDATE`.

**Tunkin Page** — paginated read of KPI Records for a single Periode. The repository JOINs `employee`, `position`, and `organization` to denormalize display fields (employee name, org name, position title) into the page rows. See ADR-0001 for why Tunkin owns this JOIN rather than calling out to the Organization domain.

**Organization** — master organization data. Read-only from the system's perspective (no write endpoints). Exposed via `GET /organization` as a public filter list for the FE Tunkin page. Also referenced by Tunkin Page reads via JOIN (see ADR-0001).

## Roles

**payrollprocess** — the menu_code guarding all Tunkin endpoints. Granted to users whose role has this menu in `sys_role_menu`.

## Out-of-scope (today)

- Organization writes (no POST/PUT/DELETE — purely filter source).
- Periode arithmetic / period-range queries (single periode only).
- Cross-periode aggregates.
