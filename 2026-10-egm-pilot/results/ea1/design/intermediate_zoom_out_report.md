# Stage 8 — Intermediate Zoom Out Review

Target: `design_draft.md` (full document)
Reviewer: `egm-zoom-out` (Skeptical Architect)

## Findings

### Major — Schema rollout remains intentionally undefined

**Affected scope:** the JPA schema and persistence sections.

The design relies on `hibernate.hbm2ddl.auto=update` and explicitly declines
migrations, backfill, conflict handling, and rollback. The reviewer notes that
production rollout of the normalized-code column, category table, and unique
constraint is therefore not described. This is an explicit project constraint:
the tables are new and the repository uses hbm2ddl rather than Flyway.

### Major — Admin and cart reads are unbounded

**Affected scope:** the unpaginated admin collection and per-cart category
resolution.

The reviewer flags response-size and N+1 risks. The design intentionally keeps
the per-store list unpaginated and does not add bulk category prefetch because
discount-code volume is expected to be small; these are recorded non-goals.

### Major — Server-local date behavior is nondeterministic across nodes

**Affected scope:** `LocalDate.now()` defaults and evaluation.

Different JVM time zones or clocks could disagree on a boundary date. The design
deliberately keeps server-local `LocalDate.now()` as the shared rule and declines
mandatory clock/time-zone configuration; a test-only `Clock` is optional if it
does not alter production behavior.

### Major — Apply and merchant edits have no concurrency protocol

**Affected scope:** apply persistence and read-time invalidation.

Separate evaluation and cart persistence can race with cart or discount edits.
The design intentionally uses last-write-wins semantics; every cart read
recalculates and repairs stale state on the next read, with no optimistic
locking or additional concurrency mechanism.

### Major — Tax base is unchanged by the merchant discount

**Affected scope:** order-total arithmetic.

The reviewer requests a tax-inclusive pricing decision. The design explicitly
keeps tax on the existing tax module's base, unchanged by this feature, while
maintaining the stated invariants: discount is non-negative, capped at the
post-variation `subTotal`, and `total` is never negative.

### Nit — Detailed implementation is intentionally low-level

**Affected scope:** the detailed implementation and test plan.

The reviewer considers the concrete class, method, mapper, exception, and test
references overly detailed. Those details are intentional because the builder
will implement directly from this document and must follow existing Shopizer
conventions.

