# Merchant-managed discount codes

* **Author:** Codex
* **Status:** Ready for build
* **Date:** 2026-10-23

## Overview

Shopizer currently recognises a hard-coded `Test1234` rule and applies a legacy one-day cart expiry. Merchants need store-owned discount codes that administrators can create, list, replace, deactivate, and delete through the private API. Shoppers must be able to apply one code to a cart, while the cart response exposes the code and the calculated discount.

The design adds a persisted, store-scoped discount entity and service, replaces the hard-coded promo calculation with that service, and recalculates the applied code whenever a cart is read. The code is retained only while it is valid for the current cart; otherwise it is cleared before the response is built.

## The Problem

The current promo path cannot express merchant-specific codes, date windows, minimum subtotals, category restrictions, or amount discounts. It also allows an expired code to remain visible for a day and has no reliable way to remove a code when cart contents or code configuration changes. A solution must preserve the existing cart endpoint while making discount ownership, validation, eligibility, rounding, and expiry explicit.

## Goals

* Persist discount codes per merchant store, with case-insensitive uniqueness within a store and the merchant-written spelling returned to clients.
* Provide the four private admin endpoints requested for create, list, replace, and delete.
* Validate required fields, type/value ranges, dates, categories, and duplicate codes with the requested HTTP statuses.
* Apply a code through `POST /api/v1/cart/{cartCode}/promo/{code}`, matching codes case-insensitively and allowing at most one applied code.
* Require store ownership, active status, inclusive start/end dates, minimum subtotal, and at least one eligible cart item before applying a code.
* Support unrestricted codes and category subtree restrictions; calculate percentage and fixed-amount discounts on eligible-item subtotals only.
* Round discount amounts to two decimal places using `RoundingMode.HALF_UP`, cap amount discounts at eligible subtotal, and make the cart total subtotal minus discount.
* Re-evaluate the applied code on every cart response; clear it and omit the discount total when it no longer applies.
* Remove the `Test1234` rule and the one-day promo expiry behavior.
* Cover persistence, validation, API status codes, eligibility, category matching, recalculation, clearing, replacement, and rounding with automated tests.

## Non-Goals

* Stacking or combining multiple codes.
* Usage counts, usage limits, redemption history, or per-customer limits.
* Free-shipping discounts or discounts on tax, shipping, or other non-item totals.
* An administrator web UI.
* Coupon generation, reporting, analytics, or audit history beyond the existing entity audit fields.
* Cross-store code sharing or global codes.
* Changes to product prices or persisted order totals outside the existing cart/order flow.
* Any special treatment for `Test1234`; the built-in rule is removed and the string has no effect unless a merchant creates it as a discount.
* Database migration tooling, rollout/backfill procedures, or schema management outside the existing Hibernate schema-generation behavior.
* Pagination, ordering guarantees, or dataset-size limits for the discount list endpoint.

## Open Questions

* None for this request. The date policy is fixed to the UTC calendar date so behavior does not depend on the application server's JVM timezone.

## Critical User Journeys (CUJs)

### CUJ 1: Administrator creates and manages a code

* **Given:** An authenticated administrator is authorised for store `store-a`.
* **When:** The administrator POSTs a valid code, lists codes, PUTs a replacement, or DELETEs an id with `?store=store-a`.
* **Then:** Create returns `201` and the stored object including `id`; list returns only `store-a` codes; replace returns the replaced object; delete removes it. A duplicate case-insensitive code returns `409`; malformed data, an unknown category/type, or an invalid date/value returns `400`; an id belonging to another store is treated as not found.

### CUJ 2: Shopper applies an eligible code

* **Given:** A cart belongs to the same store as an active code, its UTC date is inside the inclusive date range, its subtotal meets the minimum, and at least one item is in an eligible category subtree (or the code has no categories).
* **When:** The shopper posts `/api/v1/cart/{cartCode}/promo/{code}` using any letter case.
* **Then:** The response is `201 Created`, `promoCode` contains the merchant's stored spelling, `totals` contains one `discount` line with a positive value, and `total` equals undiscounted subtotal minus discount plus the existing shipping, handling, and tax amounts. Any previous code is replaced.

### CUJ 3: A previously applied code stops applying

* **Given:** A cart has an applied code.
* **When:** Items are removed, the code expires, is deactivated, is edited, or is deleted, and the cart is subsequently returned.
* **Then:** The recalculation finds no eligible code, clears the persisted promo code, returns `promoCode: null`, omits the discount line, and returns the undiscounted subtotal plus the existing shipping, handling, and tax amounts as total.

## Technical Plan (Architecture)

### Data model

Add `com.salesmanager.core.model.discount.Discount` as a JPA entity mapped to table `DISCOUNT`:

* `id` (`DISCOUNT_ID`, generated with the existing `SM_SEQUENCER` table generator).
* `merchantStore` (`MERCHANT_ID`, non-null many-to-one).
* `code` (`CODE`, non-null, length 100; preserve submitted spelling).
* `normalizedCode` (`NORMALIZED_CODE`, non-null, lower-case using `Locale.ROOT`; used only for lookup/uniqueness).
* `type` (`TYPE`, enum `PERCENT` or `AMOUNT`, persisted as string).
* `value` (`VALUE`, `BigDecimal`, scale 2 for storage; percentages are still validated as 0 < value <= 100).
* `minimumSubtotal` (`MINIMUM_SUBTOTAL`, nullable `BigDecimal`, scale 2).
* `startDate` and nullable `endDate` (`DATE` columns as `LocalDate`).
* `categories` as a many-to-many join table `DISCOUNT_CATEGORY` (`DISCOUNT_ID`, `CATEGORY_ID`).
* `active` (`ACTIVE`, non-null, default true) and the existing embedded audit section.

The table has a database unique constraint on `(MERCHANT_ID, NORMALIZED_CODE)`. The service also performs a lookup before writes and maps database constraint violations to `409 Conflict`. Category ids are store-owned; category codes are resolved and validated at write time, then the relation stores ids so renaming a category does not silently change the discount's scope.

The existing `SHOPPING_CART.PROMO_CODE` column remains the only applied-code field. The `SHOPPING_CART.PROMO_ADDED` column remains in the schema, but no code writes or reads it for expiry.

### Services and flow

```text
private Discount API
        |
        v
DiscountFacade -> DiscountService -> DiscountRepository -> DISCOUNT
        |                         \-> CategoryService (resolve/validate codes)
        |
cart promo endpoint -> ShoppingCartFacade -> DiscountService.evaluate(store, candidate, items, subtotal)
cart return/order -> OrderServiceImpl.caculateShoppingCart
                         -> set summary promoCode
                         -> caculateOrder(summary)
                         -> DiscountService.evaluate(store, summary promo, items, subtotal)
                         -> one discount OrderTotal
                         -> ReadableShoppingCartMapper (read-only)
```

`ReadableShoppingCartMapper.convert` already calls `shoppingCartCalculationService.calculate(source, store, language)` before deciding the response promo; that reaches `OrderServiceImpl.calculateShoppingCartTotal` and then `caculateShoppingCart`, so getByCode and getById responses recalculate through the same chain. The mapper must keep calling `calculate` before deciding `promoCode`, then read the possibly updated `source.promoCode`, and set the response `promoCode` to null when no `discount` total exists.

`DiscountService` owns normalization, validation, store scoping, eligibility, category matching, and discount arithmetic. Its shared contract is `Optional<DiscountEvaluation> evaluate(MerchantStore store, String code, List<ShoppingCartItem> availableItems, BigDecimal subtotal)`, where `DiscountEvaluation` contains the positive, rounded discount and the canonical stored code; an empty result means the code does not apply. The service receives the already computed subtotal and never computes a second cart subtotal. `OrderServiceImpl.caculateShoppingCart` builds the available-item list, puts the cart's code on the summary, and calls `caculateOrder`. `caculateOrder` evaluates the code once after its existing subtotal loop. If evaluation succeeds, cart calculation sets `ShoppingCart.promoCode` to `DiscountEvaluation.canonicalCode`; if it fails, it clears the field. Both changes are saved in the same transaction as totals. `ReadableShoppingCartMapper` only reads the totals produced by that flow.

Evaluation rejects inactive codes (`active == false`) and returns no result when the rounded discount is `0.00`. The cart path clears and saves the applied code in both cases; a shopper attempting to apply such a code receives `400 Bad Request`.

### Authoritative evaluation and totals contract

Every caller uses `DiscountService.evaluate(store, code, availableItems, subtotal)`. `availableItems` contains only cart lines whose product is available; each line base is stored `itemPrice × quantity`; `subtotal` is the existing `caculateOrder` subtotal including one-time additional prices before variations. The service checks store ownership, trimmed case-insensitive code, active status, UTC date window, minimum subtotal, category eligibility, and at least one eligible item. It returns `Optional.empty()` for any failed condition or a rounded-zero discount; otherwise it returns one `DiscountEvaluation` containing the positive discount amount and canonical stored code. The caller emits at most one `OrderTotal` with code `discount`. The response keeps `subtotal` undiscounted, uses `promoCode: null` when no code applies, omits the discount entry when empty, and computes final `total` as `subtotal - discount + existing shipping, handling, and tax amounts` in the current aggregation order.

`OrderTotalServiceImpl.findOrderTotalVariation` is no longer used for promo discounts. `ProcessorsConfiguration.orderTotalsPostProcessors` unregisters `PromoCodeCalculatorModule`; `PromoCodeCalculatorModule.java` is deleted. `caculateOrder` keeps its existing subtotal loop, including one-time additional prices, and evaluates `DiscountService` once when `summary.getPromoCode()` is not blank. For cart calculations, the store argument passed to `evaluate` is `shoppingCart.getMerchantStore()`. `OrderFacadeImpl` passes `shoppingCart.getMerchantStore()` to `caculateOrderTotal`; `OrderSummary` has no store field. It keeps `subTotal` as the undiscounted subtotal, emits exactly one `OrderTotal` with code `discount` and a positive value, and sets the final `total` to undiscounted subtotal minus discount before adding the existing shipping/tax totals. `Constants.OT_DISCOUNT_TITLE` is unchanged for `ManufacturerShippingCodeOrderTotalModuleImpl`; add `Constants.OT_DISCOUNT_CODE = "discount"` and use that new code for merchant discounts. The mapper's no-discount check uses `OT_DISCOUNT_CODE` and never `OT_DISCOUNT_TITLE`.

### Date and timezone

`DiscountServiceImpl` receives an injected `java.time.Clock` bean from the existing core Spring configuration. The bean returns `Clock.systemUTC()` in production. It derives `today` with `LocalDate.now(clock)`. `startDate` defaults to that UTC date on both create and PUT when omitted. A code is eligible when `today >= startDate` and (`endDate` is null or `today <= endDate`). Date-only JSON values use ISO-8601 `yyyy-MM-dd`; unit tests construct the service with a fixed clock.

### Category subtree matching

For each configured category code, resolve a category belonging to the target store and retain its id. For each product category on a cart item, split its `lineage` on `/` and discard empty tokens. The item is eligible when any token equals the id of one of the configured categories, and the product category belongs to the cart's store. This whole-token comparison handles both `/1/5/` and doubled-slash forms such as `/1//5/`; it does not use the existing substring-based `findByLineage` query. A null or empty category list is valid and treats every cart item as eligible.

Lineage tokens are compared with `Category.id.toString()`. Category codes are matched exactly as stored within the selected store; an unknown code is a `400 Bad Request`. A null or blank product-category lineage matches no configured category. The authoritative product category collection is `Product.getCategories()`, filtered to categories whose `merchantStore.id` equals the cart store id.

### Discount arithmetic

Use the exact available item list built by `OrderServiceImpl.caculateShoppingCart` (products for which `product.isAvailable()` is true). `caculateOrder` computes the cart subtotal exactly as it does today, including one-time additional prices, and passes that `subTotal` into `DiscountService.evaluate`; there is no second subtotal calculation in the service. The service sums `itemPrice × quantity` only for eligible lines to obtain `eligibleSubtotal`. The cart's own `merchantStore` is the store used for code lookup and category checks; the request's `?store` is not used for shopper eligibility. For `PERCENT`, calculate `eligibleSubtotal * value / 100`. For `AMOUNT`, use `min(value, eligibleSubtotal)`. Round the resulting discount once to scale 2 with `RoundingMode.HALF_UP`; do not round each line before summing. The returned discount is positive. The reported subtotal remains the undiscounted `caculateOrder` subtotal. The cart total is undiscounted subtotal minus discount, never below zero, before existing shipping/tax additions. Minimum-subtotal comparison uses that same undiscounted subtotal.

`availableItems` means cart line items whose product has `available=true`. Each line base is the stored `itemPrice × quantity`. The shared subtotal helper returns exactly the existing `caculateOrder` subtotal, including one-time additional prices before variations are subtracted. All callers pass these exact available items and subtotal to `evaluate`.

The response contract is explicit: when no code applies, `promoCode` is `null`; when a code applies, `totals` contains exactly one entry with `code: "discount"` and a positive `value`; when no code applies, no discount entry is present. `subtotal` is undiscounted, and `total` equals `subtotal - discount + the existing shipping, handling, and tax amounts`, using the current aggregation order.

### Authoritative contract table

| Area | Contract |
|---|---|
| Entity | `Discount`: `id`, store-scoped `merchantStore` (`@ManyToOne(fetch = LAZY)`, non-null), merchant-spelled `code` (max 100), `normalizedCode`, `type`, `value`, optional `minimumSubtotal`, `startDate`, optional `endDate`, `active`, and `categories` (`@ManyToMany`, owning side, `LAZY`, explicit `@JoinTable`, no cascade to categories). `@Table` declares the store/normalized-code unique constraint; IDs use `SM_SEQUENCER`. |
| Repository | `List<Discount> findByMerchantStore(MerchantStore store)`; `Optional<Discount> findByIdAndMerchantStore(Long id, MerchantStore store)`; `Optional<Discount> findByMerchantStoreAndNormalizedCode(MerchantStore store, String normalizedCode)`; `boolean existsByMerchantStoreAndNormalizedCodeAndIdNot(MerchantStore store, String normalizedCode, Long id)`. |
| Service | `Discount create(Discount discount, MerchantStore store)`; `List<Discount> list(MerchantStore store)`; `Discount update(Long id, Discount discount, MerchantStore store)`; `void delete(Long id, MerchantStore store)`; `Optional<DiscountEvaluation> evaluate(MerchantStore store, String code, List<ShoppingCartItem> availableItems, BigDecimal subtotal)`. The core service has no dependency on the shop DTO. |
| Facade/API | `DiscountApi` exposes create `201`, list `200`, replace `200`, and delete `200` with no body. Each method receives the `@ApiIgnore MerchantStore` resolved from `?store`; create/replace receive `@Valid PersistableDiscount` and replace receives `@PathVariable Long id`. |
| DTO | `PersistableDiscount`: response-only `Long id`; `String code` (`@NotBlank`, max 100 after trim); `DiscountType type` (`@NotNull`); `BigDecimal value` (`@NotNull`, positive); optional non-negative `minimumSubtotal`; optional ISO `LocalDate startDate` (defaults UTC today), optional `endDate`; optional null/empty `List<String> categories`; optional `Boolean active` (defaults true). |

## REST Contract and Validation

Add `DiscountApi` under `/api/v1` with the same private endpoint authentication and `MerchantStore` resolution used by existing private APIs. The `store` query parameter is the merchant store code (`String`), resolved by the same `@ApiIgnore MerchantStore` mechanism used by `TaxClassApi` (`sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/tax/TaxClassApi.java`). Copy that API's existing admin/store authorization boundary exactly. Shopper evaluation always uses the cart's own `MerchantStore`.

### DTO

Use one DTO, `PersistableDiscount`, for request and response:

```json
{
  "id": 42,
  "code": "SPRING10",
  "type": "PERCENT",
  "value": 10,
  "minimumSubtotal": 100.00,
  "startDate": "2026-01-01",
  "endDate": "2026-12-31",
  "categories": ["shoes"],
  "active": true
}
```

`id` is response-only. `active` defaults to true and `startDate` defaults to the current UTC date. `minimumSubtotal`, `endDate`, and `categories` are optional. Responses preserve the stored `code` spelling and return category codes.

PUT is a full replacement. If `active` is omitted it becomes `true`; if `startDate` is omitted it becomes today in UTC; and if `minimumSubtotal`, `endDate`, or `categories` are omitted they become null or empty, which means no minimum, no end date, or all categories. Missing `code` or `value` is a `400 Bad Request`, the same as POST. Codes are trimmed before blank validation and normalization; the trimmed spelling is stored and returned, and shopper path codes are trimmed before case-insensitive lookup.

### Endpoints and status mapping

* `POST /api/v1/private/discounts?store={store}`: validate and create; return `201 Created` with the stored DTO and id.
* `GET /api/v1/private/discounts?store={store}`: return `200 OK` with only that store's codes.
* `PUT /api/v1/private/discounts/{id}?store={store}`: replace all mutable fields; return `200 OK` with the stored DTO. The id must belong to the selected store.
* `DELETE /api/v1/private/discounts/{id}?store={store}`: delete only that store's code; return `200 OK` with no body, matching the existing private delete endpoints.

Validation and error mapping:

* `400 Bad Request`: missing/blank `code` or `value`; a trimmed code longer than 100 characters; unknown `type`; non-positive value; percentage over 100; negative `minimumSubtotal`; malformed date; end before start; category code not found in the selected store; or shopper application when any eligibility rule fails. A null/empty category list is valid. The cart remains unchanged when shopper application fails.
* `409 Conflict`: create or rename would duplicate another code in the same store after `Locale.ROOT` lower-casing. The entity's own id is excluded during PUT.
* `404 Not Found`: requested discount id is absent from the selected store; missing cart; or missing store resolved by the existing API infrastructure.
* Private endpoint access is rejected by the existing `/api/v1/private/**` security configuration and `@ApiIgnore MerchantStore` resolution used by the other private APIs; `DiscountApi` adds no authorization logic of its own.
* `500`: unexpected persistence or service failures only; validation and business failures must use typed runtime exceptions handled by `RestErrorHandler`.

Define `DiscountConflictException` and `InvalidDiscountException` in `sm-core` package `com.salesmanager.core.business.exception` as plain message-only `RuntimeException` subclasses with no dependency on `sm-shop`. `RestErrorHandler` maps them to `409` and `400`. Create and update perform a duplicate pre-check, then save and flush; any `DataIntegrityViolationException` from that save/flush becomes `DiscountConflictException` without constraint-name matching, so concurrent duplicate writes also return `409` and roll back normally. Add an explicit `@ExceptionHandler(HttpMessageNotReadableException.class)` returning `400` for unknown enum values and malformed dates (and for malformed JSON generally). Fix the catch-all handler so it uses the exception message when `getCause()` is null instead of dereferencing a null cause. `PersistableDiscount` uses the `DiscountType` enum and `LocalDate` fields; Jackson conversion failures are therefore handled explicitly as `400` before the facade is entered.

`POST /api/v1/cart/{cartCode}/promo/{code}` keeps its existing route and `201 Created` response. `ShoppingCartFacadeImpl.modifyCart` checks for a null result immediately after `shoppingCartService.getByCode`; it returns null so `ShoppingCartApi` maps the missing cart to `404` before evaluating the candidate. For an existing cart, it applies the change in memory, builds post-change available items, obtains the subtotal from the shared `OrderService` helper, evaluates the candidate without saving, throws `InvalidDiscountException` when it does not apply (mapped to `400`), and leaves the earlier code untouched. When it applies, it sets `promoCode` to the evaluation's canonical stored code, saves, and returns the cart. Matching is case-insensitive; `promoAdded` is never written. The `updateCartItems` path (current line ~663) and both existing add-item `item.getPromoCode()` paths (current lines ~767 and ~933) are transactional: they apply the item change in memory, evaluate with the shared contract, restore the earlier `promoCode` and save without raising when a candidate fails, and save once with the canonical code when it succeeds. `DiscountServiceImpl.evaluate` is transactional, so managed Product categories and lineage are available through the normal product-service repository path without a custom fetch query.

The `OrderServiceImpl.calculateShoppingCartTotal` overloads and all three mutation paths are transaction boundaries; evaluation, canonical-code persistence or restoration, and totals commit or roll back together.

For concurrent duplicates, `DiscountServiceImpl` performs the duplicate pre-check, then save and flush; any `DataIntegrityViolationException` from that save/flush becomes `DiscountConflictException` without matching constraint names. Store and category references are already validated, so the unique key is the only expected cause and the transaction rolls back normally.

## Alternatives Considered

### Keep the rules-file promo engine

* **Pros:** Minimal new persistence and reuse of existing rule evaluation.
* **Cons:** Cannot provide store-scoped CRUD, database uniqueness, category validation, or immediate deactivation/deletion semantics.
* **Reason for rejection:** It does not represent merchant-managed data and would preserve the expired hard-coded behavior.

### Store the entire discount as JSON in `SHOPPING_CART`

* **Pros:** A cart could retain a snapshot without another lookup.
* **Cons:** Edits/deletes would not invalidate existing carts, uniqueness would be difficult, and category/store validation would be duplicated.
* **Reason for rejection:** The requirements explicitly require recalculation against current code state and dropping invalid codes.

### Use a global code table without a store key

* **Pros:** Simpler lookup and one uniqueness index.
* **Cons:** Prevents two stores from using the same code and risks cross-store application.
* **Reason for rejection:** Codes are explicitly store-scoped.

## Non-Functional Requirements

* **Security:** Every admin operation is store-scoped and passes the existing private endpoint authorization. Shopper lookup always includes the cart's store id and never accepts a code entity from another store.
* **Consistency:** The `(MERCHANT_ID, NORMALIZED_CODE)` database constraint is the final guard against concurrent duplicate writes. Recalculation and clearing run in a transaction so a returned cart cannot show a code that was cleared only in memory.
* **Performance:** Load the applied code by store and normalized code and use the existing product-service repository path; query optimization is outside this feature.
* **Compatibility:** Keep existing cart JSON fields. `promoCode` is `null` when no code applies; the discount line is absent rather than zero-valued.

## Detailed Implementation Plan

### Target Files to Create/Modify

#### `sm-core-model` module

1. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/Discount.java` (Create) — JPA entity, audit section, store relation, fields above, enum mapping, normalized-code unique constraint, and category relation.
2. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountType.java` (Create) — `PERCENT` and `AMOUNT` enum.
3. `sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCart.java` (Modify) — document `promoCode` as the applied code and leave the `promoAdded` property/column unchanged for compatibility; no new code writes or reads it.

#### `sm-core` module

4. `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/DiscountRepository.java` (Create) — Spring Data queries for store list, store/id lookup, case-insensitive normalized-code lookup, and duplicate checks.
5. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountService.java` (Create) — CRUD, validation, the shared `evaluate` contract, eligibility, whole-token lineage matching, and arithmetic contract.
6. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountServiceImpl.java` (Create) — transactional implementation; inject the UTC `Clock` bean; evaluate the supplied store, code, available items, and subtotal; perform category resolution, validation including the trimmed 100-character limit, arithmetic, and typed conflict/invalid exceptions; keep Product categories and lineage managed during evaluation; after duplicate pre-check, save and flush create/update operations and translate any `DataIntegrityViolationException` from that save/flush into `DiscountConflictException` without constraint-name matching.
7. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountEvaluation.java` (Create) — immutable result containing the positive rounded discount and canonical stored code returned by `DiscountService.evaluate`.
8. `sm-core/src/main/java/com/salesmanager/core/business/configuration/ProcessorsConfiguration.java` (Modify) — remove the `PromoCodeCalculatorModule` injection and do not register it in `orderTotalsPostProcessors`.
9. `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java` (Delete) — remove the per-item promo post-processor entirely.
10. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` (Modify) — mark both `calculateShoppingCartTotal` overloads `@Transactional`; keep the existing subtotal loop, including one-time additional prices; in `caculateOrder`, call `DiscountService.evaluate(store, summary.getPromoCode(), summary.getProducts(), subTotal)` once after that loop and add one positive `OrderTotal` with `Constants.OT_DISCOUNT_CODE`; in `caculateShoppingCart`, set the cart code on the summary, call `caculateOrder`, set/save the canonical code when evaluation succeeds, clear/save it when no evaluation is returned, and remove the one-day check.
11. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderService.java` (Modify) — expose `BigDecimal calculateCartSubtotal(List<ShoppingCartItem> items)`, extracted from the existing `caculateOrder` subtotal loop, for cart mutation paths; `caculateOrder` calls this helper.
12. `sm-core/src/main/java/com/salesmanager/core/business/configuration/CoreApplicationConfiguration.java` (Modify) — register a named `Clock` bean returning `Clock.systemUTC()` for production injection.
13. `sm-core/src/main/java/com/salesmanager/core/business/constants/Constants.java` (Modify) — add `OT_DISCOUNT_CODE = "discount"` and leave `OT_DISCOUNT_TITLE` unchanged.
14. `sm-core/src/main/java/com/salesmanager/core/business/exception/DiscountConflictException.java` (Create) — plain message-only `RuntimeException` in `com.salesmanager.core.business.exception`, with no dependency on `sm-shop`.
15. `sm-core/src/main/java/com/salesmanager/core/business/exception/InvalidDiscountException.java` (Create) — plain message-only `RuntimeException` in `com.salesmanager.core.business.exception`, with no dependency on `sm-shop`.

#### `sm-shop-model` module

16. `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/PersistableDiscount.java` (Create) — the single JSON request/response DTO with validation annotations, ISO date fields, optional values/categories, and default handling.
17. `sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/ReadableShoppingCart.java` (Modify) — ensure `promoCode`, totals, and total expose the recalculated result without adding a second promo field.
18. `sm-shop-model/src/main/java/com/salesmanager/shop/store/controller/discount/facade/DiscountFacade.java` (Create) — API-facing CRUD and mapping contract using the single `PersistableDiscount` DTO.

#### `sm-shop` module

19. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountApi.java` (Create) — four private endpoints, status codes, Swagger metadata, store query handling, and typed exception propagation.
20. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/facade/DiscountFacadeImpl.java` (Create) — DTO/entity mapping, service calls, and store authorization boundary.
21. `sm-shop/src/main/java/com/salesmanager/shop/mapper/discount/PersistableDiscountMapper.java` (Create) — map the single DTO, resolve defaults, and preserve submitted code spelling while computing normalized form in the service.
22. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java` (Modify) — rewrite `modifyCart` to apply the change in memory, then evaluate using `cart.getMerchantStore()`, post-change available items, and the shared `OrderService` subtotal helper; throw `InvalidDiscountException` on failure, set the stored spelling/save on success, and retain the existing `201`; update the current line ~663 `updateCartItems` path and both current lines ~767 and ~933 `item.getPromoCode()` paths to use the same non-throwing evaluation, preserving the earlier code on failure; remove all `setPromoAdded` calls.
23. `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java` (Modify) — keep calling `shoppingCartCalculationService.calculate` before reading promo data, use `Constants.OT_DISCOUNT_CODE` when deciding whether the returned promo is represented, and set response `promoCode` to null when no discount total exists; recalculation and persistence remain in `OrderServiceImpl`.
24. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` (Modify) — retain the existing `201 Created` success response and allow `InvalidDiscountException` to map to `400` while retaining not-found handling.
25. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/order/facade/OrderFacadeImpl.java` (Modify) — remove the one-day `promoAdded` block around `calculateOrderTotal`; pass `shoppingCart.getMerchantStore()` to `caculateOrderTotal`, with the cart promo code in the order summary and no store field added to `OrderSummary`.
26. `sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/RestErrorHandler.java` (Modify) — map core `DiscountConflictException` to `409`, core `InvalidDiscountException` to `400`, `HttpMessageNotReadableException` to `400`, and fix the catch-all null-cause dereference.
27. `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl` (Delete) — remove the `Test1234` rule file outright.

Tests use `sm-shop/src/test/resources/database.properties` and `sm-core/src/test/resources/database.properties`, both with `hibernate.hbm2ddl.auto=create`; Hibernate creates `DISCOUNT` and `DISCOUNT_CATEGORY` for tests. The `Discount` entity's explicit `@Table`, `@UniqueConstraint`, `@JoinTable`, and `SM_SEQUENCER` table-generator annotations create the tables and unique constraint in the same way as other entities. Do not edit `create_schema.sql` and do not add migration files.

#### Tests

28. `sm-core/src/test/java/com/salesmanager/core/business/services/discount/DiscountServiceTest.java` (Create) — field validation, defaults, injectable UTC clock boundaries, duplicate normalization, store isolation, category validation, whole-token lineage matching including doubled slashes, percentage/amount arithmetic, cap, and HALF_UP rounding.
29. `sm-core/src/test/java/com/salesmanager/core/business/repositories/discount/DiscountRepositoryTest.java` (Create) — persistence, unique constraint, store-scoped lookup/list, and case-insensitive normalized-code queries.
30. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/discount/DiscountApiIntegrationTest.java` (Create) — authenticated CRUD endpoint status codes, single-DTO serialization, validation failures including unknown type `400`, code length over 100, conflict, and cross-store access.
31. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/cart/ShoppingCartAPIIntegrationTest.java` (Modify) — case-insensitive apply, failed apply preserves prior code, replacement, store/date/minimum/category eligibility, Test1234 no discount, exactly one `discount` line, undiscounted subtotal including additional one-time prices, drop after item removal, and drop after deactivation or deletion.
32. `sm-core/src/test/java/com/salesmanager/core/business/services/order/OrderServiceImplTest.java` (Create) — shared subtotal helper, one evaluation per `caculateOrder`, cart-code clearing, non-cart order totals, and absence of one-day expiry.
33. `sm-shop/src/test/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapperTest.java` (Create) — assert the mapper calls calculation before reading promo data, emits the canonical code with a discount total, and sets response `promoCode` to null when no `discount` total exists.

### Implementation Phases

1. **Persistence and contracts:** add the entity, enum, DTO, repository, exceptions, constants, join-table annotations, and UTC `Clock` bean. Compile the affected modules and pass persistence/DTO unit tests before continuing.
2. **Service and evaluation:** implement CRUD, validation, duplicate translation, category resolution, evaluation, rounding, and the shared subtotal helper. Compile and pass discount service/repository tests before continuing.
3. **Order and cart flow:** remove the promo post-processor and DRL, integrate one evaluation into `caculateOrder`, wire canonical-code persistence and clearing, update all three cart mutation paths, and update the mapper. Compile and pass order/cart unit and integration tests before continuing.
4. **Private API and errors:** add the CRUD facade/API, store resolution, DTO mapping, `RestErrorHandler` mappings, and malformed-input handling. Compile and pass private discount API integration tests before continuing.
5. **Legacy removal and full verification:** confirm `Test1234` has no effect unless persisted, `promoAdded` is unused, and one-day expiry is gone; run the full affected-module build and test suite. Each phase must compile and its tests must pass before the next phase starts.

### Verification Plan

* **Build:** `./mvnw -DskipTests compile` from the repository root, then compile all affected modules.
* **Unit tests:** Run the discount service, repository, cart mapper, and order service tests above; there is no promo calculator test because that class is deleted.
* **Integration tests:** Exercise authenticated private CRUD and shopper cart endpoints against the configured H2 database, including concurrent duplicate creates and cross-store ids.
* **Boundary cases:** Test UTC midnight, inclusive start/end dates, null end date, zero/negative values, 100 percent, amount greater than eligible subtotal, exact minimum subtotal, half-cent values, empty eligible categories, whole-token category lineage (including doubled slashes), and all items becoming ineligible.
* **Regression:** Verify carts without promo codes, existing totals, order creation, and stores using the same code independently.

*Drafted with EGM*
