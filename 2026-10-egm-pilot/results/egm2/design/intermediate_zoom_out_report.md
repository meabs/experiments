# Stage 8 — Intermediate Zoom Out Review

## Findings

### Major — Mapper responsibility still contradicts the clarification

**Affected scope:** Detailed Implementation Plan item 11; Review Resolution Clarifications.

The clarification makes `DiscountService` the sole calculation authority and says response mappers only project results, but item 11 still says `ReadableShoppingCartMapper` should “recalculate eligibility and totals on every read.” Rewrite item 11 so the cart calculation pipeline performs one recalculation and the mapper only renders its result.

### Major — Shopper API contract remains partially self-contained

**Affected scope:** Review Resolution Clarifications; Detailed Implementation Plan items 7 and 9.

The clarification improves CRUD semantics but omits the exact existing shopper route and request shape. The route is `POST /api/v1/cart/{code}/promo/{promo}`. State its store resolution, replacement/failure behavior, and response/error schema explicitly.

### Nit — Legacy-rule scope remains ambiguous

**Affected scope:** Detailed Implementation Plan item 12 and Review Resolution Clarifications.

“Replace hard-coded rule execution with the discount service or remove the obsolete rule path” still permits a second calculation path. State one outcome: disable/remove the legacy `Test1234` rule and prevent `PromoCodeCalculatorModule` from applying discounts independently.

## Simplicity Assessment

The earlier high-level issues are substantially resolved. Category lineage reuse, deterministic uniqueness, mapper cleanup separation, formulas, dates, security, order snapshots, and acceptance criteria are now explicit. No speculative subsystem or premature optimization was introduced.

