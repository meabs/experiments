# Goldfish Review Report

**Target:** `design_draft.md` (lines 1-311)

## Prioritized Findings (Blockers -> Major -> Nits)

### Discount aggregation has two competing paths - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `## One cart-level discount and totals` (lines 130-154); implementation items 12-13 (lines 280-287)
* **Discrepancy Description:** The design introduces a special cart-level discount path beside the existing generic per-item post-processor loop, then removes the only current processor. Future processors could be aggregated under different subtotal and discount semantics.
* **Rationale & Recommendation:** Define one explicit aggregation contract for cart-level totals and generic processors. State how future processors coexist with the discount path and how totals are combined.

### Cart reads may perform repeated calculation and writes - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `## Apply, read, and persist behavior` (lines 166-194); implementation item 8 (lines 271-276)
* **Discrepancy Description:** The shared helper is called from many paths, re-looks up and recalculates the code, and may write during a cart read. Mapper conversion then performs totals work as well. This can duplicate product/category queries and create stale-cart races.
* **Rationale & Recommendation:** Centralize cart-return recalculation in one service pipeline. Persist only when the promo state changes, and document how concurrent reads or mutations avoid overwriting a newer cart state.

### Discount pricing source is not unified with cart pricing - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `## Category and date matching` and cart-level calculation (lines 136-164, 255-258)
* **Discrepancy Description:** The discount service is described as resolving products and computing eligible subtotal, while the cart already has authoritative priced items and the order-total path resolves products and prices. Separate lookups can produce a discount that differs from the displayed cart subtotal and add duplicate work.
* **Rationale & Recommendation:** Feed the discount calculation from the existing priced cart summary or line totals. Use catalog services only for category eligibility.

### Schema decision assumes deployment behavior without a guard - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `## Persistence, schema, and private API` and implementation items 1 and 14 (lines 102-109, 248-250, 291-295)
* **Discrepancy Description:** The design treats a JPA entity as sufficient because production profiles use `hbm2ddl.auto=update`, but the test setup also initializes `create_schema.sql`. The assumption is not verified for every deployment mode.
* **Rationale & Recommendation:** Confirm the project-wide schema convention and test initialization path, or explicitly constrain the supported deployment mode and update the affected test schema.

### Architectural sections contain implementation weeds - Severity: Nit

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `## Persistence, schema, and private API` and detailed implementation plan (lines 111-128, 244-307)
* **Discrepancy Description:** Exact helper names, exception fan-out, line references, and a 14-item file list mix architecture with implementation detail.
* **Rationale & Recommendation:** Keep the high-level design focused on boundaries, data flow, contracts, and reuse. Keep file-by-file instructions in the implementation section, where they can be actionable without obscuring the architecture.
