# Goldfish Review Report

**Target:** `design_draft.md` (FeatureRange lines 1-289)

## Prioritized Findings (Blockers -> Major -> Nits)

### Total calculation contract is internally contradictory - Severity: Major

* **Reviewer Lens:** `egm-design`, `egm-style`
* **Affected Scope:** `## One cart-level discount and totals` (lines 163-180)
* **Discrepancy Description:** The draft says existing per-item variations remain subtracted from `subTotal`, then says `subTotal` remains undiscounted. It also uses phrases such as “exactly as today” and “whatever shipping and tax the existing code already adds.”
* **Rationale & Recommendation:** State one explicit calculation order and test the combination of existing variations with the new cart-level discount. Clarify which existing processors remain in scope.

### Cart-returning path coverage is unsupported - Severity: Major

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `## Apply, read, and persist behavior` (lines 213-230)
* **Discrepancy Description:** The draft asserts that the listed facade methods cover every cart-returning path, but other facade methods may return carts and are not named.
* **Rationale & Recommendation:** Audit all controller/facade paths and centralize refresh before every response, or stale promo state can be exposed.

### Hibernate auto-DDL is an unsafe production schema strategy - Severity: Major

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Persistence/schema (lines 102-110); Open Questions (lines 67-70)
* **Discrepancy Description:** The design relies on `hbm2ddl.auto=update` for a new entity, unique constraint, and element collection without a rollout, backfill, failed-DDL, or rollback plan.
* **Rationale & Recommendation:** Provide a versioned migration and rollout strategy, or explicitly document why the supported deployment contract makes auto-DDL safe. (This conflicts with the author's current schema decision and requires resolution.)

### Per-cart product/category service calls may create N+1 latency - Severity: Major

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Category matching and cart-level calculation (lines 156-160, 189-199)
* **Discrepancy Description:** Resolving every product and category on every cart response can make query count and latency grow with cart size; lazy collections may also be accessed outside their transaction.
* **Rationale & Recommendation:** Define the transaction boundary and reuse the priced summary; document batch-fetching or a query budget if this remains the chosen path.

### Over-precision money input is unspecified - Severity: Major

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Validation and money rules (lines 126-150, 182-185)
* **Discrepancy Description:** Persistence uses scale 2, but inputs with more than two decimal places are not defined. Silent database rounding could change discount behavior.
* **Rationale & Recommendation:** Explicitly reject or normalize over-precision values before persistence and define the API result.

### Negative-total behavior is not enforced - Severity: Major

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Totals and non-functional requirements (lines 171-177, 279-288)
* **Discrepancy Description:** “Never allow a negative total” has no rule for interaction with existing variations, shipping, tax, or rounding.
* **Rationale & Recommendation:** Specify whether totals are clamped, invalid upstream combinations are rejected, or existing behavior is preserved, and test boundaries.

### Concurrency is dismissed despite persisted recalculation - Severity: Major

* **Reviewer Lens:** `egm-design`, `egm-style`
* **Affected Scope:** Cart refresh (lines 213-224)
* **Discrepancy Description:** The draft calls carts “effectively single-user,” but concurrent cart updates or code edits can still produce lost writes or a response based on different state than the persisted cart.
* **Rationale & Recommendation:** Define transaction/optimistic-lock behavior or an explicit last-write-wins guarantee and consequence.

### Risk and mitigation section is missing - Severity: Major

* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** FeatureRange lines 201-248
* **Discrepancy Description:** The feature-spec standard requires explicit failure modes, security implications, scalability limits, and mitigations. The draft has non-functional requirements but no dedicated risks-and-mitigations section.
* **Rationale & Recommendation:** Add the required section if the feature-spec structure is being enforced.

### Goals are dense and combine unrelated contracts - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Goals (lines 26-58)
* **Discrepancy Description:** Endpoint, validation, eligibility, calculation, persistence, response, and legacy-rule requirements are packed into long bullets.
* **Rationale & Recommendation:** Split the goals by API, validation, eligibility/calculation, cart state, and compatibility.

### Overview uses imprecise shorthand - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Overview and The Problem (lines 11-22)
* **Discrepancy Description:** Terms such as “expired,” “protected,” “store-owned,” and “replacement semantics” are shorthand rather than observable definitions.
* **Rationale & Recommendation:** State the exact behavior and deficiency directly.

### Goal wording is ambiguous about time and mutations - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Goals (lines 41-56)
* **Discrepancy Description:** “Today,” “current cart changes,” and “renamed so it no longer matches” are less precise than the later definitions.
* **Rationale & Recommendation:** Use the same explicit timezone, lookup, and mutation terms in the goals.

### Schema and scan assertions are presented as unresolved choices - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Open Questions (lines 67-70); persistence paragraph (lines 106-109)
* **Discrepancy Description:** The schema conclusion is absolute without its deployment constraint, and “add configuration only if the actual scan excludes them” leaves a design decision open.
* **Rationale & Recommendation:** State the expected scan behavior and the explicit schema-management assumption.

### Exception-layer wording is vague - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Persistence/private API (lines 134-142)
* **Discrepancy Description:** “Thin shop facade” and “core outcomes” do not identify the translation boundary as directly as the class mappings require.
* **Rationale & Recommendation:** Name the exact catch/rethrow boundary and status mapping.

### Alternatives use broad evaluative language - Severity: Major

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Alternatives Considered (lines 257-276)
* **Discrepancy Description:** Rejection reasons such as “direct and deterministic” and “complicates” do not state concrete correctness, isolation, or performance trade-offs.
* **Rationale & Recommendation:** Tie each rejection to a specific technical consequence.

### Unpaginated GET has no operational bound - Severity: Nit

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** API schema (lines 120-126)
* **Discrepancy Description:** GET returns an unpaginated array with no record-count limit, latency target, retention policy, or index requirement.
* **Rationale & Recommendation:** Add a documented bound or pagination and the relevant operational constraint.

### Date timezone depends on deployment environment - Severity: Nit

* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Defaults/date handling (lines 34-35, 194-195)
* **Discrepancy Description:** `LocalDate.now()` in the server default zone makes date boundaries deployment-dependent.
* **Rationale & Recommendation:** Inject a clock or explicit business timezone and document the boundary test setup.

### Legacy-rule wording is emphatic - Severity: Nit

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Remove the legacy rule (lines 252-253)
* **Discrepancy Description:** “Delete outright” and “no path remains” repeat the same conclusion.
* **Rationale & Recommendation:** Name the deleted files and resulting supported path once.

### Non-functional bullets repeat earlier requirements - Severity: Nit

* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Non-Functional Requirements (lines 279-288)
* **Discrepancy Description:** Several bullets repeat requirements already stated elsewhere.
* **Rationale & Recommendation:** Retain only cross-cutting constraints not already specified, or link to the authoritative sections.
