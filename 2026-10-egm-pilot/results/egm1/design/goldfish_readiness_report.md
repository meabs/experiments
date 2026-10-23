# Goldfish Annotated Readiness Report

**Status:** resolved

**Target:** `design_draft.md` (`full file`)

## Prioritized Findings & AI Suggestions

### Issue 1 — Enumerate exact target files and symbols [egm-implementation-readiness/egm-codebase-details] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Replace wildcard targets with exact existing classes and
  explicit new paths: `PromoCodeCalculatorModule`, `OrderServiceImpl`,
  `ShoppingCartCalculationServiceImpl`, `ShoppingCartFacadeImpl`,
  `ReadableShoppingCartMapper`, `ShoppingCart`, `PromoCoupon.drl`, plus named
  discount entity/repository/service/controller/DTO/test files.

### Issue 2 — Choose one schema mechanism and exact persistence mapping [all reviewers] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Choose Hibernate schema update, remove migration-resource
  language, and specify entity/table/column names, category join table,
  nullability, cascade/delete behavior, indexes, and uniqueness handling.

### Issue 3 — Make cart persistence and concurrency actionable [egm-implementation-readiness/egm-codebase-details] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Specify `ShoppingCart.promoCode` as the persisted merchant
  string, remove `promoAdded`, add a version field with optimistic transaction
  handling, define one retry and stale-write behavior, and document apply/read/
  edit/delete flows.

### Issue 4 — Reconcile existing per-item pricing with cart-level discount [egm-codebase-details] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Define the exact change to `PromoCodeCalculatorModule` and
  `OrderTotal` production: one cart-level line, BigDecimal final prices and
  quantities, no Drools invocation, and no duplicate per-item discount entries.

### Issue 5 — Remove all legacy expiry paths [egm-codebase-details] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Name the order, facade, and mapper edits that remove
  `promoAdded` expiry/system-default timezone logic and identify the single
  invalidation/response owner.

### Issue 6 — Define promo application atomicity and API security errors [readiness/codebase] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Name the exception and JSON error mapping, transaction
  boundary, private-controller annotation/filter, role, store resolver, route,
  and cross-store/malformed-id behavior.

### Issue 7 — Add executable phases and tests [egm-implementation-readiness] — Severity: High

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Add six ordered phases with build/test checkpoints and exact
  test classes, fixtures, payloads, assertions, database setup, and Maven
  commands for all edge cases.

### Issue 8 — Clarify README and verification scope [egm-style] — Severity: Low

* **AI Suggestion:** PROPOSE FIX
* **Proposed Edit:** Name exact Maven modules/profiles and state whether README
  changes are in scope.

## Resolution Gate

Reply `auto accept` to apply all proposed fixes, `continue` to apply none, or
provide a custom instruction.
