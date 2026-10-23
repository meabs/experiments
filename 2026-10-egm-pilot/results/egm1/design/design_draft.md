# Merchant-Managed Discount Codes

*   **Author:** Codex
*   **Status:** In Review
*   **Date:** 2026-10-23

--------------------------------------------------------------------------------

## Overview

Shopizer currently recognizes a single hard-coded promo code (`Test1234`) from a
rules file. That code is expired and cannot be managed by merchants. This design
adds store-scoped discount-code records, protected private admin endpoints for
creating and maintaining them, and cart validation and pricing behavior for
shoppers applying a code.

The design keeps at most one applied code per cart. A code is re-evaluated on
every cart read, so changes to products, categories, dates, activation, or the
discount record immediately affect whether it remains applied and how much it
discounts. No code is special-cased: `Test1234` has no effect unless an admin
creates it for that store.

## Problem Statement

Merchants need to define discounts without editing deployment files, while
shoppers need predictable validation and totals. The implementation must preserve
store isolation, enforce input and date/category rules, support percentage and
fixed-amount discounts, and avoid leaving stale or invalid discounts on carts.

## Goals

* Provide authenticated, store-scoped CRUD endpoints under
  `/api/v1/private/discounts` with the specified status codes and JSON shape.
* Enforce case-insensitive uniqueness within a store while allowing the same code
  in different stores.
* Validate type, value, dates, and category references at write time.
* Apply shopper codes case-insensitively through the existing cart promo endpoint,
  with eligibility based on store, active dates, subtotal minimum, and category
  hierarchy.
* Recalculate discount and cart totals whenever a cart is returned; remove the
  code and discount line when it no longer applies.
* Round discount results to two decimal places using half-up rounding and cap
  amount discounts at eligible-item subtotal.

## Non-Goals

* Multiple simultaneous promo codes, stacking, coupons per customer, usage
  limits, or redemption analytics.
* Changes to tax, shipping, payment, catalog category administration, or currency
  conversion behavior beyond using the store's existing currency.
* Retaining the old rules-file `Test1234` behavior.

## Decisions

* Discount persistence belongs in `sm-core-model` and `sm-core`, using the
  repository's existing Hibernate schema-update mechanism; no new migration
  framework is introduced.
* `?store=` is the merchant store code resolved to `MerchantStore`; private
  endpoint authorization and store access checks are applied before any query.
* The existing `PromoCodeCalculatorModule` and
  `ShoppingCartCalculationService` remain the single pricing seam. The new
  discount lookup replaces the Drools `Test1234` branch there; no parallel
  cart-only pricing path is added.
* Category descendants are resolved with `CategoryService.getListByLineage`
  and `CategoryRepository.findByLineage`; the configured category itself is
  included, and a product matching multiple configured categories is counted
  once.
* “Today” uses the store's configured business timezone and `LocalDate`; date
  bounds are inclusive. A null `endDate` has no upper bound.
* The cart stores the merchant-written code string. A rename or deletion makes
  the next recalculation fail and clears the stored code transactionally.

## Critical User Journeys (CUJs)

### CUJ 1: Merchant creates and maintains a code

*   **Given**: An authenticated admin is operating on store `store-a`.
*   **When**: The admin posts a valid code such as `SPRING10`, then lists,
    replaces, or deletes it through the private discounts API.
*   **Then**: Creation returns HTTP 201 and includes a generated `id`; list
    returns only `store-a` codes; replacement preserves identity; deletion
    removes the resource. A duplicate in `store-a` (case-insensitive) returns
    409, while the same code in another store is allowed. Invalid input returns
    400.

### CUJ 2: Shopper applies an eligible code

*   **Given**: A cart belongs to the code's store, contains eligible products,
    meets the minimum subtotal, and the code is active within its inclusive date
    range.
*   **When**: The shopper posts to `/api/v1/cart/{cartCode}/promo/{code}` using
    any letter case.
*   **Then**: The code replaces any prior code. The cart shows `promoCode`, a
    positive `discount` total line, and `total = subtotal - discount`. Percentage
    discounts use eligible-item subtotal; amount discounts are capped at that
    subtotal and rounded half-up to two decimals.

### CUJ 3: An applied code becomes invalid

*   **Given**: A cart currently has an applied code.
*   **When**: Items change, the code is deactivated, edited, deleted, or leaves
    its date window.
*   **Then**: The next cart response re-evaluates it, clears `promoCode`, omits
    the discount line, and reports the undiscounted total. A failed new
    application returns HTTP 400 and leaves the previous code intact.

## API Contract

`DiscountRequest` and `DiscountResponse` use these fields: `id` is a server
generated long in responses; `code` is a trimmed non-empty string of at most 64
characters; `type` is `PERCENT` or `AMOUNT`; `value` is a positive decimal;
`minimumSubtotal` is an optional non-negative decimal; `startDate` defaults to
the store-local current date; `endDate` is optional and inclusive; `categories`
is an optional list of existing category codes; and `active` defaults to true.
PUT is a complete replacement, so omitted optional fields clear their previous
values and defaults are applied. Codes are compared using Unicode-independent
trimmed lowercase normalization.

| Method | Path | Success | Errors |
|---|---|---|---|
| POST | `/api/v1/private/discounts?store={store}` | 201 with stored object and `id` | 400 validation, 409 duplicate |
| GET | `/api/v1/private/discounts?store={store}` | 200 array for that store | 400 invalid store |
| PUT | `/api/v1/private/discounts/{id}?store={store}` | 200 replacement | 400 validation, 404 missing in store, 409 duplicate |
| DELETE | `/api/v1/private/discounts/{id}?store={store}` | 204 | 404 missing in store |

The shopper promo endpoint returns 400 when the code is unknown or ineligible;
the previous cart code remains unchanged. Cart responses expose an empty string
for no `promoCode`, omit the `discount` line when none applies, and retain the
existing total-line schema.

Validation rejects missing code/value, unknown type/category, non-positive
amounts, percentages outside `(0,100]`, negative minimums, and an end date
before the start date. All monetary values use the store currency's existing
decimal precision; the discount itself is rounded to two decimals half-up.

## Technical Plan (Architecture)

### Data and service layer

Add a persistent discount entity in `sm-core-model`, linked to `MerchantStore`
and containing the generated id, merchant-written code, normalized lookup form,
type enum, decimal value, optional minimum subtotal, inclusive start/end dates,
active flag, and category references. Store category codes as a relation or
validated join representation consistent with the existing catalog model.

Add repository and service operations in `sm-core` for store-scoped lookup,
case-insensitive uniqueness checks, CRUD, and eligibility evaluation. Enforce
uniqueness in both service validation and a database constraint/index on
`(store_id, normalized_code)` so concurrent creates cannot bypass the rule.
Normalize only for comparison; retain the merchant's original code for API and
cart display.

The eligibility service should:

1. Resolve the code by store and case-insensitive code.
2. Check active state, the store-local inclusive date window, and cart subtotal
   minimum over the full merchandise subtotal before category filtering.
3. Resolve configured category codes and descendants, then sum only matching cart
   items (or all items when no categories are configured).
4. Return no discount when the eligible subtotal is zero.
5. Compute percentage or capped amount discount with `BigDecimal`, scale 2, and
   `RoundingMode.HALF_UP`; for example, an eligible subtotal of 0.01 with a 50%
   rate yields 0.005, represented as 0.01.

### Admin API

Add a private controller in `sm-shop` following existing `/api/v1/private`
controller authorization and `?store=` resolution. Map request/response DTOs for
the stated JSON fields, default `active=true` and `startDate=today`, and return
201/200/204 for successful create/list/update/delete operations. Translate
validation failures to 400 and duplicate normalized codes to 409. Update and
delete must load by both id and resolved store so an admin cannot affect another
store's record.

### Cart application and presentation

Extend the cart promo operation to call the eligibility service before mutating
the cart. On failure, throw the existing API-level bad-request path without
changing the current applied code. On success, replace the single stored code.

Extend `PromoCodeCalculatorModule` inside the existing
`ShoppingCartCalculationService` pipeline. The module resolves the stored code,
computes the positive discount line once, and lets the existing order-total
processor subtract it from merchandise subtotal before tax and shipping are
calculated. `ReadableShoppingCartMapper` exposes the resulting lines and total.
`ShoppingCartFacadeImpl.getByCode`, `getById`, customer-cart reads, item
mutation responses, and `OrderFacadeImpl` all delegate to this calculation seam;
legacy one-day `promoAdded` expiry checks are removed.

When recalculation finds the stored code invalid, it clears the code in the same
transaction as the cart update (or with an optimistic version check); a stale
concurrent clear is retried and never overwrites a newer applied code.

```text
Admin request -> private discount controller -> discount service/repository
                                      |
Shopper promo endpoint -> eligibility service <- cart items + category tree
                                      |
Cart read -> recalculate/clear -> readable cart totals (promoCode, discount, total)
```

## Alternatives Considered

### Alternative A: Keep promo definitions in the rules file

*   **Pros**: Minimal code and no schema migration.
*   **Cons**: No merchant administration, no store isolation, no per-code
    lifecycle, and impossible to satisfy CRUD or concurrent uniqueness.
*   **Reason for Rejection**: It directly conflicts with the requested operating
    model and leaves the expired hard-coded behavior in place.

### Alternative B: Store only the applied discount amount on the cart

*   **Pros**: Cart reads avoid a code lookup.
*   **Cons**: Edits, deletion, date changes, category changes, and item changes
    cannot be re-evaluated safely; stale totals would persist.
*   **Reason for Rejection**: The requirements explicitly require recalculation
    and automatic removal whenever eligibility changes.

### Alternative C: Store a discount id instead of the merchant-written code

*   **Pros**: Referential integrity and direct lookup.
*   **Cons**: Renames require joins and deletion requires nullable foreign-key
    handling; old carts may lose the display text.
*   **Reason for Rejection**: The response must display the merchant-written
    code, and deletion must invalidate without a dangling reference.

### Alternative D: Calculate only when the shopper applies the code

*   **Pros**: Fewer reads and simpler cart responses.
*   **Cons**: Edits, dates, catalog changes, and deactivation leave stale
    discounts.
*   **Reason for Rejection**: Recalculation on every returned cart is required.

## Traceability

| Requirement | CUJ | Verification |
|---|---|---|
| Store-scoped CRUD and conflict handling | CUJ 1 | Admin API integration tests |
| Eligibility, categories, dates, and rounding | CUJ 2 | Discount service unit tests |
| Replacement failure preserves prior code | CUJ 2 | Cart API failure test |
| Invalidation after edits, deletion, or item changes | CUJ 3 | Cart recalculation integration tests |
| No hard-coded `Test1234` behavior | CUJ 1 and CUJ 3 | Legacy regression test |

## Non-Functional Requirements

*   **Security and tenancy**: Every admin query and mutation must be constrained
    by the resolved merchant store. Never trust a client-supplied store id when
    loading an id for update or delete. Reuse the existing private API
    authentication and authorization filters.
*   **Consistency**: Database uniqueness must back up application checks. Cart
    code replacement and invalidation should be transactional with cart writes so
    a failed validation cannot partially replace the prior code.
*   **Money correctness**: Use decimal arithmetic only; do not use binary
    floating point. Apply half-up rounding at the final discount calculation and
    preserve the store's currency scale conventions.
*   **Performance**: Cart reads should fetch one discount and bounded category
    data per cart, with repository queries for descendant categories rather than
    scanning all products. Add indexes for store/code and active date lookups.
*   **Compatibility**: Existing carts without a promo code must serialize exactly
    as before apart from the permitted empty `promoCode` representation. The
    rules-file code path must be removed or bypassed.

## Risks & Mitigations

*   **Duplicate pricing**: Keep one calculation seam in
    `PromoCodeCalculatorModule`; remove the Drools `Test1234` branch and legacy
    one-day expiry checks.
*   **Cross-store access**: Resolve `?store=` and cart ownership before every
    query; return authorization failure without revealing another store's ids.
*   **Concurrent edits and applies**: Use transactional writes and optimistic
    cart version checks; map database uniqueness violations to 409.
*   **Category-tree drift**: Resolve descendants at calculation time through the
    existing lineage service, so catalog edits take effect on the next cart
    response.
*   **Read-time invalidation failure**: If the cart version changes during a
    clear, return the recalculated current state and retry once rather than
    overwriting a newer code.

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/*` (Create)

*   Add the discount entity, type enum, category association, and persistence
    metadata. Include store relation, normalized code, optional fields, dates,
    active flag, and generated id.

#### 2. `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/*` and `.../services/discount/*` (Create)

*   Add store-scoped repository methods and a service that validates input,
    enforces normalized uniqueness, resolves category descendants, evaluates
    eligibility, and computes rounded discounts.

#### 3. Database migration resources under the existing `sm-core` migration/configuration path (Create)

*   Create discount and category-link tables, foreign keys, indexes, and the
    case-insensitive-per-store uniqueness constraint required by the project’s
    database setup.

#### 4. `sm-shop/src/main/java/com/salesmanager/shop/.../private...` discount controller and DTO packages (Create)

*   Implement POST/GET/PUT/DELETE routes, store resolution, DTO defaults, and
    201/400/409/404/204 mappings using established private-controller patterns.

#### 5. Existing cart promo controller, cart service, and readable-cart mapper in
`sm-shop` and `sm-core`

*   Replace hard-coded promo handling with discount-service lookup; persist only
    the applied code reference/value needed for re-resolution. Recalculate on
    every cart-return path and update totals and `promoCode` output.

#### 6. `sm-core/src/test`, `sm-shop/src/test`, and integration-test fixtures (Create/Modify)

*   Cover validation, uniqueness, store isolation, category descendants,
    date boundaries, rounding, amount capping, replacement failure atomicity,
    cart invalidation, and removal of `Test1234` special behavior.

### Verification Plan

*   **Compilation/Build**: `./mvnw -DskipTests compile` and the affected module
    test builds.
*   **Unit tests**: Discount service tests for every validation and calculation
    rule, including `0.005` half-up cases and category-tree eligibility.
*   **Integration tests**: Mock or embedded database tests for CRUD status codes,
    store isolation, and concurrent duplicate creation; API tests for cart
    application and response totals.
*   **Regression checks**: Existing shopping-cart and order-total test suites;
    verify carts without codes and carts containing legacy `Test1234`.
*   **Manual verification**: Exercise create, rename conflict, deactivate,
    delete, item removal, and date-boundary scenarios through the API.

## Implementation Readiness Addendum

### Exact target files and symbols

Modify the existing symbols in:

* `sm-core-model/.../shoppingcart/ShoppingCart.java` — replace the legacy
  `promoAdded` state with persisted `promoCode` and add an optimistic `version`.
* `sm-core/.../modules/order/total/PromoCodeCalculatorModule.java` — resolve
  merchant discounts and emit one cart-level `OrderTotal` discount line.
* `sm-core/.../business/services/order/OrderServiceImpl.java` and
  `sm-core/.../business/services/shoppingcart/ShoppingCartCalculationServiceImpl.java`
  — remove one-day expiry and route all calculations through the module.
* `sm-shop/.../store/facade/shoppingCart/ShoppingCartFacadeImpl.java`,
  `sm-shop/.../store/controller/order/facade/OrderFacadeImpl.java`, and
  `sm-shop/.../store/controller/shoppingCart/ReadableShoppingCartMapper.java`
  — use the shared calculation result and remove duplicate promo checks.
* `sm-core/.../modules/order/total/PromoCoupon.drl` and its
  `DroolsBeanFactory` registration — remove the `Test1234` rule and registration.

Create `discount/Discount.java`, `discount/DiscountType.java`,
`discount/DiscountCategory.java`, the matching repository/service classes in
`sm-core`, request/response DTOs and `DiscountApi` in `sm-shop`, and named unit
and integration test classes beside the existing module tests.

### Selected persistence and transaction behavior

Use Hibernate schema update only. Create `DISCOUNT` with columns `ID`,
`STORE_ID`, `CODE`, `NORMALIZED_CODE`, `TYPE`, `VALUE`, `MINIMUM_SUBTOTAL`,
`START_DATE`, `END_DATE`, and `ACTIVE`; create `DISCOUNT_CATEGORY` with
`DISCOUNT_ID` and `CATEGORY_ID`. Add a unique `(STORE_ID, NORMALIZED_CODE)`
constraint and foreign keys with cascade on discount deletion and restrict on
category deletion. Category codes are resolved to category ids at write time;
deleted categories make the discount invalid on the next edit/read.

Persist `ShoppingCart.promoCode` as the merchant-written string and remove
`promoAdded`. Add a numeric version column. Apply and invalidation operations
run in one transaction; an optimistic-lock conflict retries once, then returns
the latest cart without overwriting a newer code.

### Pricing and API error behavior

`PromoCodeCalculatorModule` is the sole monetary calculator. It sums final item
prices times quantities into a `BigDecimal`, filters eligible items once, rounds
the single discount line half-up to scale 2, and passes that line to the
existing order-total pipeline before tax and shipping. The mapper emits the
positive line exactly once. Invalid promo application raises the existing
bad-request exception mapped to HTTP 400; no cart mutation occurs. Private
discount routes use the existing private-controller annotation and store
resolver, return 403 for denied store access, 404 for an id absent from the
resolved store, and the standard JSON error body for malformed ids and database
conflicts.

### Phased checkpoints

1. **Model/schema** — add entities and Hibernate mappings; run core compilation.
2. **Repository/service** — add validation, category lookup, and calculation;
   pass service unit tests.
3. **Admin API** — add controller/DTOs and status/error tests; pass shop tests.
4. **Cart pricing** — replace module rule path and mapper behavior; pass cart and
   order-total tests.
5. **Legacy removal** — delete Drools rule/registration and expiry branches;
   pass legacy regression tests.
6. **Integration** — run API/cart/database suites and verify all traceability
   cases before merge.

Test targets are `DiscountServiceTest`, `DiscountApiTest`,
`PromoCodeCalculatorModuleTest`, `ShoppingCartDiscountIntegrationTest`, and
`DiscountConcurrencyTest`, using the existing `AbstractSalesManagerCoreTestCase`
fixtures and project H2/database profile. Run `./mvnw -pl sm-core,sm-shop test`
and the configured integration-test profile; all tests and existing regression
suites must pass.
