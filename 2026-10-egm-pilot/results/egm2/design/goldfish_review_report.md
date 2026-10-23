# Goldfish Annotated Review Report

**Status:** resolved

Stage 9 proposed fixes accepted and applied to `design_draft.md`.

**Target:** `design_draft.md` (full file)

## Prioritized Findings & AI Suggestions

### Issue 1 — Define one calculation boundary [Zoom Out / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Justification:** Multiple existing total components plus the new service could double-apply discounts.
*   **Proposed Edit:** State that `DiscountService` is the sole eligibility/calculation authority; cart and order total pipelines invoke it once, and mappers only project results.

### Issue 2 — Remove mapper write side effects [Zoom Out / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Justification:** Read mapping must remain a pure projection; invalid-code cleanup belongs in a transactional cart write/calculation path.
*   **Proposed Edit:** Move invalid-code clearing to the cart service and define transactional behavior; mapper omits discount data when the service returns no applicable discount.

### Issue 3 — Reuse category lineage services [Zoom Out] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Justification:** Existing category lineage infrastructure avoids bespoke traversal.
*   **Proposed Edit:** Require reuse of `CategoryService.getListByLineage` / `CategoryRepository.findByLineage` and existing indexes.

### Issue 4 — Deterministic uniqueness and normalization [Zoom Out / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Justification:** Service-only duplicate checks race under concurrent writes.
*   **Proposed Edit:** Add normalized trimmed code, project migration/index, unique-constraint error mapping to 409, and length/Unicode normalization rules.

### Issue 5 — Complete API contracts [Comprehension] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Add method/path, auth/store binding, request/response schema, PUT replacement semantics, list behavior, 404/400/409 error schema, and cart promo endpoint details.

### Issue 6 — Specify discount formulas and money rules [Comprehension / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** State percentage bounds, eligible-item subtotal formula, amount cap, decimal scale, half-up rounding point, and boundary tests.

### Issue 7 — Specify date/category/subtotal semantics [Comprehension / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Define timezone/end-of-day behavior, category self+descendant matching, deletion/move handling, subtotal exclusions, and indexed lineage query behavior.

### Issue 8 — Define cart/order lifecycle [Comprehension / Critic] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Define reference versus display spelling, delete/deactivate behavior, transactional cleanup, concurrent checkout, and immutable order snapshot semantics.

### Issue 9 — Add Heilmeier cost, timeline, and metrics [Critic] — Severity: Medium

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Add effort/operational impact estimates, milestones, and acceptance metrics for correctness, latency, authorization, and regression.

### Issue 10 — Align implementation paths and limits [Zoom Out / Critic] — Severity: Low

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Reconcile paths with repository conventions and define pagination, validation limits, and stable error payloads.

## Stage 9 Readiness Findings

### Issue 11 — Choose repository-aligned persistence [Readiness / Codebase] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Specify Hibernate schema-update entities and exact table/column/index/foreign-key mappings; remove the nonexistent migration wildcard.

### Issue 12 — Close API and DTO contracts [Readiness / Style] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Name concrete modules/classes, fields/types/nullability, routes, pagination envelope, and error codes.

### Issue 13 — Define existing calculation-pipeline integration [Codebase] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Add `ShoppingCartCalculationServiceImpl` and `ProcessorsConfiguration` to the exact change list; make `DiscountService` the sole invocation path.

### Issue 14 — Specify cart persistence fields and lifecycle [Readiness] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Define discount ID/reference and display-spelling fields, ORM mappings, null/delete behavior, and explicit write-time cleanup.

### Issue 15 — Make tests and commands executable [Readiness / Style] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Name exact test classes/cases, fixtures/assertions, concurrency and schema tests, and fixed Maven commands.

### Issue 16 — Remove contradictory alternatives [Readiness / Style] — Severity: High

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Require disabling/removing the legacy rule and retain `promoAdded` only as an ignored compatibility field, with no one-day expiry logic.

### Issue 17 — Set numeric limits and measurable thresholds [Style] — Severity: Low

*   **AI Suggestion:** PROPOSE FIX
*   **Proposed Edit:** Define concrete code/category/page limits, error codes, currency source, test commands, and latency/acceptance thresholds.
