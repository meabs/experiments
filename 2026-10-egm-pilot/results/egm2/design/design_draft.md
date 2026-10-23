# Store-Managed Discount Codes

*   **Author:** Codex
*   **Status:** Proposed
*   **Date:** 2026-10-23

--------------------------------------------------------------------------------

## Overview

Shopizer currently recognizes a single hard-coded promo code in its rules file. That code is expired and cannot be managed by merchants. This design adds store-owned discount codes managed through protected admin APIs and applied by shoppers to carts.

Each store can create, list, replace, and delete its own codes. Codes support percentage or fixed-amount discounts, optional date, subtotal, and category restrictions, and an active flag. Shoppers can apply one valid code to a cart. The cart recalculates the discount whenever it is returned, so changes to products, carts, or codes take effect without leaving stale discount values.

## The Problem

Merchants cannot create or control promotion codes. The current hard-coded `Test1234` behavior is not suitable for production: it is shared by every store, expired, and disconnected from merchant administration. Shoppers also need predictable behavior when a code is invalid, expires, is edited, or no longer matches the cart.

The feature must provide store-scoped code management, case-insensitive uniqueness and application, clear validation errors, category-aware eligibility, correct monetary rounding, and consistent cart totals. A failed application must not disturb a code already on the cart; a valid application replaces the previous code. The legacy hard-coded code must have no effect unless a merchant explicitly creates it.

## Goals

*   Let authenticated store administrators create, view, replace, and delete discount codes through `/api/v1/private/discounts` endpoints scoped by `?store=`.
*   Validate code definitions and return the specified HTTP status codes, including conflict responses for duplicate codes within a store.
*   Allow shoppers to apply one case-insensitive code through the existing cart promo endpoint.
*   Apply percentage and fixed-amount discounts only when store, active status, dates, subtotal, category eligibility, and value rules all pass.
*   Recalculate discounts whenever a cart is returned and remove a code when it no longer applies.
*   Expose the merchant-entered code, discount total, and discounted cart total consistently in cart responses.
*   Remove the implicit discount behavior of `Test1234`.

## Non-Goals

*   Building a new merchant-admin user interface; this design covers the API and domain behavior only.
*   Supporting multiple simultaneous promo codes on one cart.
*   Adding customer-specific, usage-count, per-order, or campaign reporting rules.
*   Changing the store currency model or adding currency conversion.
*   Preserving existing hard-coded `Test1234` discounts or introducing a migration that creates that code automatically.

## Technical Plan (Architecture)

Add a persisted discount aggregate linked to `MerchantStore`, with a case-insensitive uniqueness constraint enforced in the service and database where supported. Store the code as entered for display, while using a normalized form for lookup and conflict checks. Persist type, decimal value, optional minimum subtotal, inclusive dates, active state, and category associations.

Expose a private-admin controller and DTOs for CRUD operations. Resolve `?store=` through the same merchant-store and authorization path used by existing private APIs. Map validation failures to HTTP 400 and duplicate codes to HTTP 409; return the created representation with its generated `id` and HTTP 201.

Centralize eligibility and amount calculation in a discount service used by both promo application and cart response calculation. The service must load the cart's store, resolve the case-insensitive code, evaluate active/date/subtotal/category conditions, select eligible line items including descendants of configured categories, and calculate a rounded discount using half-up rounding. A failed application returns 400 without changing the cart's existing code. A successful application stores only the selected code reference (and preserves the merchant-entered spelling) and replaces any prior code.

Cart mapping/calculation must re-evaluate the stored code on every read. If it is missing, inactive, outside its dates, invalid for the current subtotal, or has no eligible items, clear the applied reference and omit the discount total. Otherwise emit `promoCode`, a positive `discount` total line, and `total = subtotal - discount`. Remove the one-day `promoAdded` expiry rule.

The existing Drools rule containing `Test1234` must be removed or disabled so it cannot create a discount independently of the persisted-code service.

```text
Admin request (?store=)
        |
        v
Discount controller -> Discount service -> Discount repository
                                      |              |
                                      +--> category repository

Cart promo request ------------------>+ (validate and attach code)
Cart read -> cart calculation -> discount service -> totals mapper
```

Likely integration points are the core model/repository/service layers, the shop private API and DTO mapping layers, `ShoppingCart` calculation and readable-cart mapping, and the existing promo rule and cart integration tests. Exact file additions and modifications are enumerated in the Detailed Implementation Plan.

## Alternatives Considered

### Keep promo definitions in the rules file

*   **Pros**: Minimal persistence and code changes; existing Drools execution remains in place.
*   **Cons**: Merchants cannot manage codes, codes cannot be scoped safely per store, and date/category/cart re-evaluation becomes difficult to make consistent.
*   **Reason for Rejection**: It does not meet the core requirement for merchant-managed, store-specific codes and would preserve the expired hard-coded behavior.

### Store one complete discount snapshot on the cart

*   **Pros**: Cart reads would avoid loading the current discount definition and recalculating eligibility.
*   **Cons**: Editing or deactivating a code would leave stale values and would require synchronization or cleanup jobs.
*   **Reason for Rejection**: The requirements explicitly require recalculation on every cart return and removal when the code no longer applies.

### Allow several promo codes per cart

*   **Pros**: More expressive promotions and potentially higher merchant flexibility.
*   **Cons**: Ordering, stacking, caps, rounding, and conflict behavior become ambiguous; the requested contract specifies at most one code.
*   **Reason for Rejection**: It expands scope and conflicts with the one-code cart invariant.

### Use a global code table with store filtering only in application logic

*   **Pros**: A single lookup table and simpler cross-store reporting.
*   **Cons**: Uniqueness and authorization boundaries become easier to violate, and every query must reliably include store scoping.
*   **Reason for Rejection**: A store-owned relationship and store-scoped uniqueness make isolation explicit and reduce cross-store leakage risk.

## Detailed Implementation Plan

### Target Files to Create/Modify

1. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/Discount.java` (Create) — Persist the code, type, value, store, dates, active flag, minimum subtotal, and category links.
2. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountType.java` (Create) — Define `PERCENT` and `AMOUNT`.
3. `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/DiscountRepository.java` (Create) — Store-scoped and case-insensitive lookup, list, and duplicate checks.
4. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountService.java` and `DiscountServiceImpl.java` (Create) — Validate definitions, enforce uniqueness, resolve categories, evaluate eligibility, calculate half-up discounts, and perform CRUD.
5. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/Discount.java` (Modify) — Use the project’s Hibernate schema-update convention to create the discount table and category join table from explicit entity mappings: non-null store/code-normalized/type/value/start/active columns, nullable end/minimum columns, foreign keys, and a store-plus-normalized-code unique constraint.
6. `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/DiscountRequest.java` and `DiscountResponse.java` (Create) — Define exact JSON names and types: `String code`, `DiscountType type`, `BigDecimal value`, nullable `BigDecimal minimumSubtotal`, `LocalDate startDate/endDate`, `List<String> categories`, `Boolean active`, and response `Long id`; default active/start values as specified.
7. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountApi.java` (Create) — Implement the repository’s existing API package and security annotations for POST/GET/PUT/DELETE at `/api/v1/private/discounts` and `/api/v1/private/discounts/{id}`, with explicit `store`, `page`, and `size` parameters and standard error responses.
8. `sm-shop/src/main/java/com/salesmanager/shop/store/facade/discount/DiscountFacade.java` and `DiscountFacadeImpl.java` (Create) — Bridge authorized API calls to the core service and map the exact request/response DTOs.
9. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java` and `ShoppingCartFacade.java` (Modify) — Validate promo application before mutating the cart, replace prior codes, and remove one-day expiry handling.
10. `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCart.java` (Modify) — Add nullable `Long discountId` and retain `promoCode` as display text; retain `promoAdded` for schema compatibility but stop reading or writing it for eligibility and remove all one-day expiry logic.
11. `sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartCalculationServiceImpl.java` and `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java` (Modify) — Perform the single discount recalculation in the calculation service; the mapper only renders its returned totals and never mutates persistence.
12. `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java`, `ProcessorsConfiguration.java`, and `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl` (Modify) — Disable/remove the legacy processor and rule entirely; `DiscountService` is the only discount calculator and `Test1234` has no implicit effect.
13. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` and `sm-shop/src/main/java/com/salesmanager/shop/store/controller/order/facade/OrderFacadeImpl.java` (Modify) — Remove one-day promo expiry checks and use the shared discount calculation when order totals are prepared.
14. `sm-core/src/test/java/com/salesmanager/test/shoppingcart/ShoppingCartTest.java` and new `DiscountServiceTest.java` (Modify/Create) — Assert every validation/formula/date/category/store-isolation case, including concurrent duplicate creation and deleted categories.
15. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/discount/DiscountAPIIntegrationTest.java` (Create) — Assert exact JSON, 201/204/400/404/409 bodies, pagination, forged-store rejection, and PUT replacement.
16. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/cart/ShoppingCartAPIIntegrationTest.java` (Modify) — Assert `POST /api/v1/cart/{code}/promo/{promo}` success/rejection/replace behavior, recalculation after cart/code edits, totals, persistence cleanup on write, and no `Test1234` discount.

### Verification Plan

*   **Compilation/Build**: Run `./mvnw -DskipTests install`, then `./mvnw test` from the repository root; both must pass.
*   **Unit Tests**: Run discount service and calculation tests, including decimal half-up cases and inclusive date boundaries.
*   **Integration Tests**: Run private discount API and cart API integration tests against a store with products in nested categories.
*   **Regression Checks**: Verify carts without codes, carts with deleted/deactivated codes, order totals, and stores using the same code independently.
*   **Security Checks**: Verify an authenticated admin cannot read or mutate another store’s discounts by changing `?store=` or an ID.

*   **Schema/Concurrency Checks**: Verify Hibernate creates the declared tables/indexes and concurrent duplicate creates produce one resource and one 409 response.

## Review Resolution Clarifications

*   **Authoritative calculation**: `DiscountService` is the sole authority for code lookup, eligibility, and discount arithmetic. The cart/order total pipeline invokes it once per calculation; response mappers only project the returned result and never write to persistence. Existing Drools promo execution is removed from this path.
*   **Cart lifecycle**: A cart stores the discount ID plus the merchant-entered display spelling. Reads recalculate without mutation. An explicit cart write/calculation transaction clears an invalid reference; concurrent updates use the cart’s normal optimistic/versioned save behavior. Order creation recalculates once and stores immutable order totals and the applied code spelling.
*   **API contract**: `POST /api/v1/private/discounts` returns 201 and the complete resource including `id`; `GET` returns the store’s paginated list; `PUT /api/v1/private/discounts/{id}` is full replacement; `DELETE` returns 204. All routes require the existing private-admin authentication and bind the authenticated principal to `?store=` and the resource’s store. Cross-store IDs return 404. Validation errors use 400, duplicate normalized codes use 409, and errors use the project’s standard error body.
*   **Shopper promo contract**: `POST /api/v1/cart/{code}/promo/{promo}` resolves the cart’s store, validates the code before mutation, leaves an existing code unchanged on 400, and replaces it on success; it returns the standard readable-cart response or standard 400 error body.
*   **Code normalization and uniqueness**: Trim input, apply Unicode-aware case folding, enforce a maximum length of 64 characters, retain the original spelling for responses, and persist a normalized value with a store-scoped unique index. Catch unique-index violations and map them to 409.
*   **Discount formulas**: `PERCENT` accepts `(0,100]`; `AMOUNT` accepts values greater than zero. Subtotal is the current cart merchandise subtotal before this discount, excluding shipping and tax. Eligible subtotal is the sum of current eligible line-item extended prices. Percentage discount is `eligibleSubtotal * value / 100`; amount discount is `min(value, eligibleSubtotal)`. Round the final discount once to currency scale (2 decimals) using half-up rounding, never exceeding eligible subtotal.
*   **Dates and categories**: Date-only start/end values are interpreted in the store timezone, with both boundaries inclusive and `endDate` meaning the end of that local day. Omitted end dates are unbounded. A configured category and all descendants qualify; multiple categories are combined by union. Current category lineage is evaluated on each calculation using the existing `CategoryService.getListByLineage` / `CategoryRepository.findByLineage` infrastructure and its indexes. Missing or deleted category references make the definition invalid for application.
*   **Security and limits**: Store identity is derived and checked server-side for every CRUD operation; client-supplied store values cannot grant access. Limit categories to 50 per code and list pages to size 100; return stable error codes `INVALID_DISCOUNT`, `DISCOUNT_CONFLICT`, and `DISCOUNT_NOT_FOUND`. Tests cover forged store parameters and IDs.
*   **Operational acceptance**: Milestones are schema/service/API, cart integration, then regression hardening. Acceptance exams require all formula/date/category tests to pass, exactly-once discount application, zero cross-store authorization failures, no implicit `Test1234` discount, and cart-read latency within the existing cart calculation budget. The implementation is expected to require one focused engineering iteration plus integration-test hardening; storage is one discount row plus category links per code.
