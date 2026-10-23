# Goldfish Review Report

**Target:** `design_draft.md` (lines 1-359)

## Prioritized Findings (Blockers -> Major -> Nits)

### Schema rollout remains an unresolved risk - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Open Questions (lines 67-70); implementation item 14 (lines 338-343)
* **Discrepancy Description:** The draft relies on Hibernate `update` for the entity, unique constraint, and element collection without a rollout or failure strategy.
* **Rationale & Recommendation:** Specify the supported schema-management contract or provide versioned migration and rollback handling. This finding conflicts with the stated project convention and requires an explicit acceptance decision.

### The v1 customer-cart path is not covered by the helper - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Cart refresh (lines 213-240); implementation item 8 (lines 317-323)
* **Discrepancy Description:** `ShoppingCartApi` delegates customer reads to `shoppingCartFacadev1.get`, which reaches the legacy facade's `readableCart` path. The design names the legacy facade paths but does not make the shared helper available to both facades, and its primary implementation path may be misnamed.
* **Rationale & Recommendation:** Centralize refresh at a service boundary used by both facades and enumerate every customer-cart endpoint.

### Mapper and helper still duplicate calculation and persistence - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Cart refresh and mapper changes (lines 226-240)
* **Discrepancy Description:** The helper refreshes before mapping, while `ReadableShoppingCartMapper` calls `ShoppingCartCalculationService.calculate`; that service invokes order calculation and persists the cart on every call. The state-change-only helper rule does not prevent mapper-triggered writes or repeated work.
* **Rationale & Recommendation:** Define one calculation/persistence pipeline and make mapping read-only.

### Last-write-wins semantics remain under-specified - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Cart refresh (lines 219-229)
* **Discrepancy Description:** Concurrent cart mutations or discount edits can produce a stale response that overwrites newer promo/cart state.
* **Rationale & Recommendation:** Define transaction/optimistic-lock behavior, or explicitly constrain and test the accepted last-write-wins semantics.

### Total aggregation and negative-total behavior remain contested - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Cart-level totals (lines 157-185); non-functional requirements (lines 283-288)
* **Discrepancy Description:** The draft defines special discount handling while retaining other variation subtraction, and still states a non-negative-total requirement without a separate enforcement rule.
* **Rationale & Recommendation:** Verify the explicit aggregation order against `OrderServiceImpl` and test all variation/shipping/tax combinations. If the stated discount bounds are the complete guarantee, remove any broader unimplemented non-negative-total claim.

### Category lookups still scale with cart items - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Cart-level calculation and category matching (lines 157-180, 189-199)
* **Discrepancy Description:** Category eligibility still requires product/category lookups per item, and the transaction boundary for lazy category access is not stated.
* **Rationale & Recommendation:** Define the transaction boundary and reuse existing item-loop lookups; document the accepted small-cart assumption.

### Risks and mitigations remain implicit - Severity: Major

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Entire document, especially non-functional requirements (lines 279-288)
* **Discrepancy Description:** There is no dedicated failure-mode and mitigation section for schema rollout, stale writes, authorization failures, or query growth.
* **Rationale & Recommendation:** Add explicit risks and mitigations if the feature-spec standard is required. This is a structural finding previously declined by the author.

### Detailed plan remains implementation-heavy - Severity: Nit

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Detailed plan (lines 294-343)
* **Discrepancy Description:** Exact helper names, exception fan-out, and file-by-file edits remain in the document.
* **Rationale & Recommendation:** Keep the architectural contracts and mechanical implementation instructions distinct if the document will serve both audiences.

### Server timezone remains deployment-dependent - Severity: Nit

* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Date handling (lines 34-35, 194-195)
* **Discrepancy Description:** `LocalDate.now()` in the server default zone makes validity boundaries depend on deployment timezone.
* **Rationale & Recommendation:** Inject a clock or define a business timezone and test the boundary explicitly. This is a stated product decision in the current draft.
