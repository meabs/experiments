# Goldfish Review Report

**Target:** `design_draft.md` (FeatureRange lines 1-243; DetailedRange lines 244-313)

## Prioritized Findings (Blockers -> Major -> Nits)

### API schemas are not defined - Severity: Blocker

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Goals/API contract (lines 26-40); implementation items 5-7 (lines 266-277)
* **Discrepancy Description:** The draft names the endpoints and says POST/PUT return a complete shape, but does not define request/response JSON field types, nullability, ID type, list wrapper, pagination, or DELETE content type.
* **Rationale & Recommendation:** Add the exact request and response schemas so an implementer does not have to infer the external contract.

### Validation ranges and normalization are incomplete - Severity: Blocker

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Validation rules (lines 32-40, 120-128); implementation item 4 (lines 262-265)
* **Discrepancy Description:** “Invalid value” does not define PERCENT limits, AMOUNT limits, scale/precision, type/code normalization, malformed-date format, or validation-error precedence.
* **Rationale & Recommendation:** State every permitted range, date format, scale, normalization rule, and deterministic precedence for multiple invalid fields.

### Discount and total formulas are not fully reproducible - Severity: Blocker

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Goals and totals (lines 41-56, 130-158)
* **Discrepancy Description:** The draft does not say whether `10` means 10% or a fraction, how intermediate arithmetic is scaled, or enough about shipping/tax to reproduce totals without consulting code.
* **Rationale & Recommendation:** Define the percentage interpretation, intermediate precision/rounding, and the exact existing shipping/tax total inputs used by `OrderServiceImpl`.

### Entity mapping and storage choices are underspecified - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Persistence/schema (lines 102-109); implementation item 1 (lines 255-257)
* **Discrepancy Description:** Monetary Java types/precision, category-code collection storage and ordering, ID generation/type, store relation fetch/cascade behavior, and recomputation of `codeNormalized` on updates are not fixed.
* **Rationale & Recommendation:** Specify these observable schema and persistence choices.

### Authorization boundary is not concrete - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Private API (lines 115-118, 242-243); item 6 (lines 269-271)
* **Discrepancy Description:** “Authenticated allowed admin group” and `authorizedStore` do not state required groups, missing/malformed `store` behavior, multi-store access, or whether list filtering matches PUT/DELETE.
* **Rationale & Recommendation:** Name the groups and store-resolution/authorization outcomes for every endpoint.

### Error response contracts are absent - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Error handling (lines 36-40, 120-128); CUJ 1 (lines 74-80)
* **Discrepancy Description:** Status codes are given, but error payloads, field attribution, malformed IDs, missing store context, repository failures, and uniqueness-race behavior are not defined.
* **Rationale & Recommendation:** Specify the observable error body and translation behavior, including database uniqueness races.

### Cart refresh order and coverage are incomplete - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Cart refresh (lines 170-201); item 8 (lines 278-283)
* **Discrepancy Description:** The helper's listed methods may not be all cart-returning paths, and invocation order relative to mutation, totals, mapping, failed persistence, and unchanged promo state is not defined.
* **Rationale & Recommendation:** Enumerate the complete public path set and define refresh, calculation, persistence, and mapping order.

### Category lookup and malformed lineage behavior are unclear - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Category eligibility (lines 160-168); item 4 (lines 262-265)
* **Discrepancy Description:** Product category retrieval, missing associations, duplicate configured categories, ID type, null/malformed lineage, and exact boundary handling are not fully described.
* **Rationale & Recommendation:** Define those cases and the category collection normalization rules.

### Uniqueness races lack a translation contract - Severity: Major

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Persistence consistency (lines 105-109, 244-245)
* **Discrepancy Description:** Service normalization and a database constraint are specified, but transaction/isolation and handling of a concurrent constraint violation are not.
* **Rationale & Recommendation:** Require catching the constraint failure and translating it to 409.

### Empty shopper promo input is ambiguous - Severity: Nit

* **Reviewer Lens:** `egm-comprehension`
* **Affected Scope:** Goals/apply behavior (lines 47-55, 172-180)
* **Discrepancy Description:** The draft does not state whether an empty or whitespace promo path clears an existing code or returns 400.
* **Rationale & Recommendation:** Choose and document one observable behavior.
