# Stage 5 — Initial Zoom Out Review

## Findings

### Major — Multiple discount calculation paths

**Affected sections:** Technical Plan; Detailed Implementation Plan items 9–13.

The proposal introduces a discount service while retaining several existing total participants (`PromoCodeCalculatorModule`, `OrderServiceImpl`, `ShoppingCartCalculationServiceImpl`, and `ReadableShoppingCartMapper`). Recalculating in multiple layers risks inconsistent totals and unnecessary persistence side effects. Define one authoritative calculation boundary and have cart/order responses consume that result.

### Major — Read mapping must not perform cleanup writes

**Affected sections:** Technical Plan; Detailed Implementation Plan item 11.

Clearing a persisted code from `ReadableShoppingCartMapper` makes a presentation mapper stateful and couples reads to writes, creating transaction and concurrency risks. Invalid-code cleanup belongs in the cart/domain calculation service; the mapper should remain a pure projection.

### Major — Reuse existing category lineage infrastructure

**Affected sections:** Technical Plan; Detailed Implementation Plan items 1, 4, 5, and 8.

The repository already provides category lineage support such as `CategoryService.getListByLineage` and `CategoryRepository.findByLineage`. Reuse that infrastructure instead of introducing bespoke descendant traversal.

### Major — Specify deterministic case-insensitive uniqueness

**Affected sections:** Technical Plan; Detailed Implementation Plan items 3 and 5.

“Database where supported” leaves correctness dependent on deployment details, while a service-only check is race-prone. Specify the project’s migration/database convention and use a normalized-code column/index, or explicitly document the supported database limitation.

### Nit — Align proposed paths with repository conventions

**Affected sections:** Detailed Implementation Plan items 7 and 8.

The proposed private API path does not match the repository’s established API layout, and the new facade package lacks a concrete analogue. Reuse existing private API/facade conventions and merchant-store authorization resolution.

### Nit — Define the subtotal source

**Affected sections:** Overview and Goals.

The statement that product and cart changes take effect leaves line-item price and subtotal semantics implicit. Identify the existing order/cart calculation as the single source for subtotal and eligible line-item prices.

## Stage Result

The design addresses the requested root problem, but the calculation boundary, mapper side effects, category reuse, and uniqueness mechanism require revision before proceeding to later review stages.

