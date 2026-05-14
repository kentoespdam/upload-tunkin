# Domain Context — Upload Tunkin

Domain vocabulary. Architectural terms (Module, Seam, Adapter, Depth) live in `/improve-codebase-architecture` — this is *what we model*, not *how we structure*.

## Core terms

- **Periode** — payroll period `YYYYMM` (e.g. `202605`). Path param for `GET /tunkin/{periode}`. Opaque string; no date arithmetic.
- **NIPAM** — *Nomor Induk Pegawai* at PDAM. Natural employee ID. Filter in `TunkinRequest`; part of `(periode, nipam)` natural key in `salary_kpi`.
- **KPI Record** — row in `salary_kpi`: `periode`, `nipam`, `nominal`. Unique on `(periode, nipam)`.
- **KPI Upload** — Excel pipeline: `FileGate` → `KPISheetParser` → batch upsert. Triggered by `POST /tunkin/upload`, orchestrated by `UploadKpiCommand` (CQRS, also CLI-callable). Idempotent via `ON DUPLICATE KEY UPDATE`.
- **Tunkin Page** — paginated KPI Records for one Periode. Repo JOINs `employee`, `position`, `organization` to denormalize display fields. Tunkin owns this JOIN — see [ADR-0001](docs/adr/0001-tunkin-owns-organization-join.md).
- **Organization** — master org data. Read-only domain (`app/organization/`). Exposed via `GET /organization` as FE filter list. Also read by Tunkin via JOIN (ADR-0001).

## Roles

- **payrollprocess** — `menu_code` guarding all Tunkin endpoints. Granted via `sys_role_menu`.

## Out-of-scope

- Organization writes (filter source only).
- Periode arithmetic / range queries (single periode only).
- Cross-periode aggregates.
