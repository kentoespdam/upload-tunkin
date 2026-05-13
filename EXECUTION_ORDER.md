# Architecture Refactor — Execution Order

Issues from the architectural review, ordered from first to last. Run `bd show <id>` for full details on any item.

## 1. `upload-tunkin-ufj` — Wire repositories and helpers through FastAPI `Depends`

- **Type:** AFK
- **Blocked by:** none
- **Why first:** every later slice that needs a test seam relies on `Depends`-based injection. Cheap, mechanical, low blast radius.

## 2. `upload-tunkin-iw6` — Move Sqids ID encoding to the HTTP edge; make encoding deterministic *(HITL)*

- **Type:** HITL — on-wire ID format will change after removing the `datetime.now()` noise from `SqidsHelper.encode`. Confirm no external client depends on the current encoded format before merging.
- **Blocked by:** none (independent of the auth/upload work — can run in parallel with #1)
- **Why early:** unrelated to the auth chain, so it can land any time once approval is granted. Listed second because it is the only HITL item and its approval cycle may run alongside #1.

## 3. `upload-tunkin-c5m` — Split `TokenHelper` into `TokenIssuer` and `TokenVerifier`; break cycle with `SysUserRepository`

- **Type:** AFK
- **Blocked by:** `upload-tunkin-ufj` (#1)
- **Why here:** unblocks the permission-checker work and removes the circular import. Needs #1 so the new classes can be injected via `Depends`.

## 4. `upload-tunkin-g7z` — Extract `PermissionChecker` so authorization is testable without FastAPI

- **Type:** AFK
- **Blocked by:** `upload-tunkin-c5m` (#3)
- **Why here:** consumes the new `TokenVerifier`. Lands authorization as a pure-function module with unit tests.

## 5. `upload-tunkin-rsp` — Split the Excel upload monolith into `FileGate`, `KPISheetParser`, `KPIRepository.upsert_batch`

- **Type:** AFK
- **Blocked by:** `upload-tunkin-ufj` (#1)
- **Why here:** highest-leverage refactor on the riskiest code path. Independent of the auth chain — can be tackled in parallel with #3 and #4 once #1 is done.

## 6. `upload-tunkin-5i3` — Consolidate the `HTTPException` → `ResponseBuilder` mapping into a single registry

- **Type:** AFK
- **Blocked by:** none (technically), but cleanest after #4 since auth errors are the main consumer
- **Why last:** smallest leverage, highest locality gain. Pairs well with the auth work, but standalone if you need a quick win first.

## Dependency graph (text form)

```
ufj ──┬── c5m ── g7z
      └── rsp

iw6   (independent, HITL)
5i3   (independent, low priority)
```

## Suggested working order

1. `upload-tunkin-ufj` *(start here — unblocks the most)*
2. `upload-tunkin-c5m`
3. `upload-tunkin-g7z`
4. `upload-tunkin-rsp` *(can run parallel with #2/#3 once #1 lands)*
5. `upload-tunkin-iw6` *(any time once HITL approval is in hand)*
6. `upload-tunkin-5i3` *(last; cleanest after #3 since it touches auth error shape)*
