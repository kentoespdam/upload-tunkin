# ADR-0001: Tunkin Page reads own their JOIN to `organization`

**Status:** Accepted
**Date:** 2026-05-13

## Context

After the domain-module refactor, `organization` becomes its own domain with its own repository (`app/organization/repository.py`) feeding `GET /organization` as a FE filter list.

`TunkinRepository.fetch_page_data()` already JOINs `position` → `organization` to denormalize the org name into Tunkin Page rows. The question raised during the refactor: should Tunkin keep that JOIN, or should it call `OrganizationRepository` to enrich each page row?

## Decision

**Tunkin keeps the JOIN.** `OrganizationRepository` is only used by `GET /organization` and by any future caller that needs the *list of organizations as entities*. It is **not** the gateway through which Tunkin reads organization names.

## Why

- The denormalized org name on a Tunkin Page row is **Tunkin's read concern**, not Organization's. It exists to render a payroll-period table, not to represent an Organization.
- Going through `OrganizationRepository` to enrich page rows means either N+1 queries or a second SELECT + Python-side join. The JOIN is one query and lets MySQL do what it's good at.
- Strict domain isolation would force every cross-domain read through a repository, which inverts the cost: it makes "obvious" queries expensive to satisfy a purity goal that delivers no testability or locality benefit here.

## Consequences

- The `organization` table is referenced by SQL in **two** repositories (`tunkin/repository.py` and `organization/repository.py`). This is intentional, not duplication-to-eliminate.
- If the `organization` table schema changes (column renamed, dropped), both repositories must be updated. Acceptable cost — schema changes already require migrations and are visible.
- Future architecture reviews may flag this as a layering violation. They should re-read this ADR before suggesting a "fix."

## What would change this decision

- If organization rows acquired invariants enforced at the application layer (computed fields, permission-filtered visibility, audit-on-read), Tunkin would need to go through `OrganizationRepository` to inherit those invariants. At that point, revisit.
