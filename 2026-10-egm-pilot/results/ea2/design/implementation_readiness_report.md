# Goldfish Review Report

**Target:** `design_draft.md` (DetailedRange lines 305-374)

## Prioritized Findings (Blockers -> Major -> Nits)

### Concrete DTO and mapper files are not enumerated - Severity: Major

* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Implementation item 5 (lines 320-322)
* **Discrepancy Description:** “list/mapper classes” is an unspecified file set. The plan does not identify which class owns request binding, response mapping, or collection output.
* **Rationale & Recommendation:** Name every concrete production path and its responsibility.

### Test files and assertions are not concrete - Severity: Major

* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Implementation item 14 and Verification Plan (lines 353-370)
* **Discrepancy Description:** “Discount/cart/API test packages” leaves test placement, harness, fixtures, and assertions to the implementer.
* **Rationale & Recommendation:** Name concrete test classes or paths, use the existing integration support and fixtures, and specify expected response bodies/statuses for each required case.

### Authorization behavior is not an executable predicate - Severity: Major

* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** API item 6 and private API description (lines 126-129, 323-325)
* **Discrepancy Description:** “Allowed admin group,” `authorizedStore`, and `?store=` do not name accepted groups or behavior for missing, malformed, unauthorized, or multi-store store context.
* **Rationale & Recommendation:** State the exact existing group set and status outcome for each endpoint context.

### Exception translation lacks a complete matrix - Severity: Major

* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** Items 4, 7, and cart apply behavior (lines 139-147, 210-218, 326-331)
* **Discrepancy Description:** CRUD uses typed core exceptions while apply uses generic `ServiceRuntimeException`; the exact mapping for each failure, including missing cart versus missing discount, and the shared error body is not listed in the implementation section.
* **Rationale & Recommendation:** Add an exception-to-status/body matrix and exact catch/rethrow boundary.

### Discount service contracts are not specified - Severity: Major

* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** Items 4, 8, and 10 (lines 316-319, 332-338, 342-346)
* **Discrepancy Description:** The plan names responsibilities but not concrete method inputs/outputs, the no-discount result, applicability result, or construction contract for the positive `OrderTotal`.
* **Rationale & Recommendation:** Define the service method contracts and null/empty semantics before implementation.

### `getById` store scoping is not explicit in the file plan - Severity: Major

* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** Item 8 (lines 332-338); `ShoppingCartFacadeImpl.getById`
* **Discrepancy Description:** The current method loads by id without a store predicate, while the design requires store-scoped access.
* **Rationale & Recommendation:** Require a store-scoped ID lookup and 404 for an id missing from or belonging to another store.

### Category lookup and lineage algorithm need exact calls - Severity: Major

* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** Items 4 and 14 (lines 316-319, 353-358)
* **Discrepancy Description:** “Resolve categories” and “match lineage” do not name the exact `CategoryService.getByCode(MerchantStore, code)` call or define duplicate configured codes, null product categories, and malformed lineage behavior in the implementation steps.
* **Rationale & Recommendation:** State the lookup call and the exact eligibility algorithm and edge-case outcomes.

### Existing API test infrastructure is not named - Severity: Nit

* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** Verification Plan (lines 360-370)
* **Discrepancy Description:** The plan does not name existing support such as `ServicesTestSupport.java` and `ShoppingCartAPIIntegrationTest.java`, or the authentication, store, cart, and product fixtures.
* **Rationale & Recommendation:** Reference the existing harness and fixture setup for reproducible integration coverage.
