# Merchant-Managed Discount Codes

*   **Author:** OpenAI
*   **Status:** Approved
*   **Date:** 2026-10-23

--------------------------------------------------------------------------------

## Overview

Shopizer currently stores a cart promo string, but the only discount is the
expired, hard-coded `Test1234` Drools rule. This design adds store-owned
discount records, protected CRUD endpoints, and one cart-level discount that is
validated and recalculated from current data whenever a cart is returned.

## The Problem

Merchants cannot manage their own codes. The current facade imposes a one-day
`promoAdded` lifetime, the order-total processor calculates a discount once per
item, and the Drools rule has no store, date, minimum, category, amount, or
replacement semantics. Cart output also treats the discounted amount as part of
the reported subtotal, which conflicts with `total = subtotal - discount`.

## Goals

* Add protected, store-scoped `POST /api/v1/private/discounts` (201 with the
  stored object and `id`), `GET /api/v1/private/discounts`, `PUT
  /api/v1/private/discounts/{id}`, and `DELETE /api/v1/private/discounts/{id}`.
  POST and PUT return the same complete shape (`id` and every field); PUT
  returns 200; DELETE returns 200 with an empty body, matching private delete
  endpoints such as `TaxClassApi`.
* Support `code`, `type` (`PERCENT` or `AMOUNT`), `value`, optional
  `minimumSubtotal`, optional `endDate`, optional category codes, `active`, and
  `startDate`. POST and PUT default `active=true` and `startDate=LocalDate.now()`
  in the server default zone.
* Return 400 for a missing or whitespace-only code, missing value, unknown type,
  malformed date, invalid value, end date before start date, or a category code
  absent from the requested store. Enforce case-insensitive uniqueness per store
  on create and rename with 409; re-saving the same record under its own name,
  even with different case, is allowed. The same code may exist in other stores.
* Apply a code only when it belongs to the cart store, is active, today is in
  the inclusive start/end range, the cart's undiscounted subtotal meets the
  minimum, and at least one item is eligible. Category eligibility includes the
  configured category and all descendants.
* Calculate `PERCENT` from eligible-item subtotal and cap `AMOUNT` at that
  subtotal. Round the final discount to two places using `HALF_UP`.
* Match shopper input ignoring case. A non-applying code returns 400 and leaves
  the previous code untouched; an applying code replaces it, so a cart has at
  most one code.
* Return the stored discount's spelling in `promoCode`, a positive `discount`
  total line, the undiscounted item subtotal in `subtotal`, and a total formed
  from that subtotal minus the discount plus the existing shipping and tax
  totals (or simply `subtotal - discount` when neither exists). Recalculate on
  every cart-returning path; if the code is edited, deactivated, deleted,
  renamed so it no longer matches, or the cart changes, clear it and omit the
  discount line. There is no one-day expiry.
* Delete the `Test1234` rule. It has no effect unless a merchant creates that
  code record.

## Non-Goals

* Stacking codes; usage or redemption limits; shopper-specific codes.
* An administrator UI.
* Changes to other promotion, tax, shipping, or pricing rules beyond replacing
  the `Test1234` rule and integrating this discount.

## Open Questions

None. Profiles use `hibernate.hbm2ddl.auto=update`, while tests use `create`, so
the JPA entity is sufficient and no migration script is required.

Accepted constraints: use the existing auto-DDL convention; allow last-write-wins
cart concurrency; use the server default timezone; omit a separate risks
section; and retain the current implementation-detail level.

## Critical User Journeys (CUJs)

### CUJ 1: Administrator manages a code

*   **Given**: An authenticated administrator is authorized for store `S`.
*   **When**: The administrator creates, lists, replaces, or deletes a code.
*   **Then**: Only `S` is affected; status and response shape follow the API
    contract; invalid input is 400, duplicate code is 409, and an id missing or
    owned by another store is 404 for PUT and DELETE.

### CUJ 2: Shopper applies an eligible code

*   **Given**: A cart in `S` has an eligible item, meets the undiscounted
    minimum, and the code is active and in its inclusive date range.
*   **When**: The shopper posts `/api/v1/cart/{cartCode}/promo/{code}`.
*   **Then**: The matched record's spelling is stored, it replaces any prior
    code, and the response has one positive discount and a reduced total.

### CUJ 3: A code stops applying

*   **Given**: A cart has a code.
*   **When**: Items, categories, dates, value, active state, or the record
    change, or the record is deleted or renamed.
*   **Then**: The next cart response clears and persists `promoCode` and omits
    the discount line. A rejected replacement leaves the old code in place.

## Technical Plan (Architecture)

### Persistence, schema, and private API

Create a JPA `Discount` entity related to `MerchantStore`, with the entered
`code`, a `codeNormalized` column containing the upper-cased code, type/value,
optional minimum/end date/category-code collection, active flag, and start date.
Put a unique constraint on `(merchant_id, code_normalized)`. Existing entity
scanning in `DataConfiguration` uses
`factory.setPackagesToScan("com.salesmanager.core.model")`, which covers
`com.salesmanager.core.model.discount`. Existing Spring Data repository
scanning covers `com.salesmanager.core.business.repositories.discount`.
Hibernate creates/updates the table in deployments and creates it in tests.

The entity id is a `Long` using the same table-generator style as other
Shopizer entities. Its store relation is `@ManyToOne(fetch = LAZY)` with no
cascade. Categories are an `@ElementCollection` of code strings in a join
table; duplicates are removed and order has no meaning. `codeNormalized` is set
on every create and update as `code.trim().toUpperCase(Locale.ROOT)`.

Add `DiscountRepository` and `DiscountService`/`DiscountServiceImpl` for
store-scoped CRUD, normalized lookup, validation, conflict detection, and
applicability. Add `DiscountApi` under
`sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/`.
`MerchantStoreArgumentResolver` resolves `?store=` exactly as it does for
`TaxClassApi`; the existing Spring Security configuration protects
`/api/v1/private/**`, and the resolver handles missing or unknown stores. No
additional authorization logic is added.

The request JSON is `code` string; `type` string exactly `PERCENT` or `AMOUNT`;
`value` number; nullable `minimumSubtotal` number; nullable `startDate` and
`endDate` strings in `yyyy-MM-dd`; nullable/empty `categories` array of category
code strings; and nullable `active` boolean, where null means true. The response
has the same fields plus numeric `id` (`Long`), with `startDate` and `active`
always filled in. GET returns a plain array with no wrapper or pagination.
DELETE returns 200 with an empty body.

`sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/PersistableDiscount.java`
binds the request.
`sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/ReadableDiscount.java`
is the response and
includes `id`. `DiscountFacade` and `DiscountFacadeImpl` in
`sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/facade/`
convert DTOs and entities and
translate core exceptions into shop exceptions. GET returns
`List<ReadableDiscount>`. There are no other mapper or list classes.

`PersistableDiscount` binds `type`, `startDate`, and `endDate` as strings, not
Jackson enum/date fields. The core `DiscountServiceImpl` throws
`DiscountValidationException`, `DiscountConflictException`, and
`DiscountNotFoundException`, all core `ServiceException` subtypes. `DiscountApi`
(or its thin shop facade) catches those core outcomes and rethrows shop-layer
`ServiceRuntimeException`/`ConflictException`/`ResourceNotFoundException`.
`RestErrorHandler` maps them to 400, 409, and 404 respectively. Thus the core
module never depends on sm-shop exceptions, and unknown types or malformed dates
cannot fall through to a generic 500 response.

Validation stores the code trimmed; a blank code is 400. `value=10` means 10%:
PERCENT requires `0 < value <= 100`, AMOUNT requires `value > 0`, and a negative
`minimumSubtotal` is 400. Money fields use `BigDecimal` with precision 19 and
scale 2. If several fields are invalid, return 400 for whichever check fails
first; the exact order is not significant. Catch
`DataIntegrityViolationException` on save and translate it to the core conflict
outcome, then to the shop 409 response.
The core service contracts are `Discount create(Discount, MerchantStore)`,
`Discount update(Long id, Discount, MerchantStore)`, `void delete(Long id,
MerchantStore)`, and `List<Discount> list(MerchantStore)`. It also exposes
`Optional<Discount> findApplicable(String code, ShoppingCart or OrderSummary
items, MerchantStore)`, returning empty when the code does not apply, and
`Optional<OrderTotal> calculateDiscount(OrderSummary, MerchantStore, Language)`.
When the latter returns a total, `orderTotalCode = Constants.OT_DISCOUNT_TITLE`,
`module = "discount"` (or the existing discount module constant), `title =
"discount"`, `text` is the discount code, `orderTotalType = SUBTOTAL`, and
`value` is the positive discount.

Exception translation is fixed: core validation becomes 400 via
`ServiceRuntimeException`; core conflict or `DataIntegrityViolationException`
becomes 409 via `ConflictException`; core not-found becomes 404 via
`ResourceNotFoundException`. On the cart promo endpoint, a missing cart is 404
and a missing or non-applicable code is 400. All use the existing
`ErrorEntity` body.
Values of `value` or `minimumSubtotal` with more than two decimal places are
400; input is never rounded.

### One cart-level discount and totals

Choose the cart-level path: remove `promoCodeCalculatorModule` from
`ProcessorsConfiguration.orderTotalsPostProcessors()`, delete
`PromoCodeCalculatorModule`, and have `OrderTotalServiceImpl.findOrderTotalVariation`
call `DiscountService` once per `OrderSummary`, outside the per-item loop. The
service receives `summary.getProducts()`, resolves each product with
`ProductService`, and returns at most one `OrderTotal` with code
`Constants.OT_DISCOUNT_TITLE` (`discount`) and a positive value. The existing
per-item loop remains for any other post-processors added later; an empty
post-processor list is already handled by `OrderTotalServiceImpl` by returning
an empty variation.

In `OrderServiceImpl`, a variation whose `orderTotalCode` is
`Constants.OT_DISCOUNT_TITLE` is added to `orderTotals` but is not subtracted
from `subTotal`. Any other variation is still subtracted from `subTotal` as
today; none exist after the promo module is removed. Then compute
`grandTotal = subTotal - discount`, and add shipping and tax exactly as the
existing code does. The discount cannot exceed eligible subtotal, and eligible
subtotal cannot exceed subtotal, so no clamp is needed. Both the
minimum-subtotal check and eligible subtotal use the priced `ShoppingCartItem`
values already present in `OrderSummary`, multiplying price by quantity exactly
as `OrderServiceImpl` does; `ProductService` and `CategoryService` are used
only to decide category eligibility. Keeping the `discount` line in
`orderSummary.getTotals()` preserves the mapper's existing check for whether a
code applies.

The formulas are `eligibleSubtotal * value / 100`, then `setScale(2, HALF_UP)`
for PERCENT, and `min(value, eligibleSubtotal)`, then `setScale(2, HALF_UP)`
for AMOUNT. Do not round between these operations. Shipping and tax remain
exactly as `OrderServiceImpl` handles them today.

### Category and date matching

Load configured categories by code with `CategoryService` for the cart's store;
missing categories are rejected at CRUD time. A product can have several
categories. A product category matches configured category C when it is C or
its `Category.lineage` contains `/<C.id>/` (lineage format is `/1/5/`). Any
matching product category makes the item eligible. With no configured
categories, every item is eligible. Use `LocalDate.now()` in the server default
zone and compare both start and end inclusively.

Read product categories from `Product.getCategories()`. Load configured
categories with `CategoryService.getByCode(MerchantStore, String)` and remove
duplicate configured codes. A product with no categories is ineligible when the
code is restricted to categories. A null product category list is not eligible.
A null or malformed lineage matches only the category itself. The
`DiscountService` method that
computes the cart discount is `@Transactional`, so product categories and
category lineage can be read there. Carts are assumed to be small, and
per-item product lookups are acceptable.

### Apply, read, and persist behavior

In `ShoppingCartFacadeImpl.modifyCart(String cartCode, String promo, ...)`,
load the code for the cart's store ignoring case and ask `DiscountService` to
validate it against the complete cart before changing anything. Unknown,
cross-store, inactive, out-of-range, below-minimum, or no-eligible-item cases
throw `ServiceRuntimeException`; `ShoppingCartApi` already routes that to 400
through `RestErrorHandler`. Check for a missing cart first so it still returns
404. On success, save the matched record's own `code` (not the shopper's
spelling), set `promoAdded` only as legacy data if needed, and keep the current
endpoint success status (201).

Add one shared `ShoppingCartFacadeImpl` helper, for example
`refreshPromoCodeAndPersist(ShoppingCart, MerchantStore, Language)`, used by
`getByCode`, `getById(Long, ...)`, `getCart(Customer, ...)`, `readableCart`,
both `addToCart` overloads, both `modifyCart` overloads, `modifyCartMulti`, and
`removeShoppingCartItem` when it returns a cart. The
promo overload `modifyCart(String, String, ...)` validates before saving and
then uses the helper for its response. The helper looks up the stored cart code
again by this store ignoring case, recalculates applicability, and, when the
promo state changes, clears `ShoppingCart.promoCode` or corrects its spelling
and saves the cart. It does not save when the promo state is unchanged. It also
ensures the response uses the matched record's current spelling. Carts are
effectively single-user; if concurrent writes occur, last write wins.

Each listed cart-returning facade method follows this order: mutate and save the
cart, run the refresh helper (look up the code again; if it no longer applies or
its spelling differs, update `promoCode` and save), then map through
`ReadableShoppingCartMapper`, which calculates totals. These are the
cart-returning paths. The promo path
variable is required, so an empty or whitespace promo cannot occur; blank input
is a 400.

The v1 customer-cart facade delegates to the legacy facade's `readableCart(...)`,
which is already on this refresh list, so the v1 facade needs no change.

`ShoppingCartCalculationService.calculate` already saves the cart on every call;
that existing behavior is accepted. The mapper remains otherwise unchanged
apart from the specified `promoCode` changes, including this extra save.

Change `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`:
remove its one-day `promoAdded` check (around line 113), set
`destination.setPromoCode(source.getPromoCode())` from the matched spelling
saved by the helper, and retain its existing behavior that sets `promoCode` to
null when no `discount` total is present (around line 263). Do not put
persistence in the mapper. Remove the separate one-day check in
`ShoppingCartFacadeImpl.getByCode`.

```text
private API -> DiscountService -> repository -> store + normalized code
cart promo POST -> store/case/date/minimum/category validation -> save matched code
cart-return helper -> case-insensitive relookup -> applicability -> clear+save if stale
summary -> OrderTotalServiceImpl (once) -> positive discount line
                         -> OrderServiceImpl: total = undiscounted subtotal - discount
```

### Remove the legacy rule

Delete `PromoCoupon.drl` outright and delete `PromoCodeCalculatorModule`; no
Drools rule or promo-code KIE path remains.

## Alternatives Considered

### Keep Drools and generate rules per merchant

*   **Pros**: Reuses the current KIE integration.
*   **Cons**: Runtime rule generation complicates CRUD, store isolation, and
    cart-wide category and amount calculations.
*   **Reason for Rejection**: A transactional discount service is direct and
    deterministic.

### Store the full discount object in the cart

*   **Pros**: Avoids a lookup on read.
*   **Cons**: Edits, deactivation, deletion, and renames would not propagate.
*   **Reason for Rejection**: The requirement needs live recalculation and stale
    code removal.

### Keep the one-day `promoAdded` expiry

*   **Pros**: Small change to current behavior.
*   **Cons**: Conflicts with validity lasting as long as the code applies.
*   **Reason for Rejection**: The discount's dates and current cart state define
    validity.

## Non-Functional Requirements

*   **Security**: Private calls require authenticated admin role and store
    authorization; all shopper and id lookups are store-scoped.
*   **Consistency**: Normalize to upper case in service code and enforce the
    `(store, code_normalized)` database uniqueness constraint.
*   **Money**: Use `BigDecimal`, two-place `HALF_UP` rounding, and never allow a
    discount greater than eligible subtotal. Because eligible subtotal is less
    than or equal to subtotal, the discount cannot make the total negative.
*   **Compatibility**: Keep existing cart JSON fields; omit the discount line
    and clear `promoCode` when no current code applies.

## Detailed Implementation Plan

### Target Files to Create/Modify

1. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/Discount.java`
   (Create): JPA fields, `code_normalized`, store relation, category-code
   collection, dates, active flag, and unique `(merchant_id, code_normalized)`.
2. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountType.java`
   (Create): `PERCENT` and `AMOUNT` constants; API input remains a string DTO.
3. `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/DiscountRepository.java`
   (Create): store/id and store/normalized-code queries.
4. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountService.java`
   and `DiscountServiceImpl.java` (Create): parse string fields, apply defaults,
   validate all 400 rules, throw conflict/not-found outcomes, resolve categories,
   match lineage, and calculate one cart-level discount.
5. `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/PersistableDiscount.java`
   and `ReadableDiscount.java` (Create): bind string type/date request fields
   and define the complete response shape including id. No other mapper or list
   classes are created. Add `DiscountFacade.java` and `DiscountFacadeImpl.java`
   under `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/facade/`
   to convert DTOs/entities and translate core exceptions.
6. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountApi.java`
   (Create): four endpoints, 201/200 responses, DELETE 200 with an empty body,
   and private admin checks.
7. `sm-core/src/main/java/com/salesmanager/core/business/exception/DiscountValidationException.java`,
   `DiscountConflictException.java`, and `DiscountNotFoundException.java`
   (Create): core `ServiceException` subtypes; plus
   `sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/ConflictException.java`
   and `RestErrorHandler.java` (Create/Modify): translate core outcomes in
   `DiscountApi`/shop facade and map them to 400/409/404.
8. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`
   (Modify): pre-save validation in `modifyCart(String, String, ...)`,
   matched-record spelling, removal of one-day checks, and shared
   `refreshPromoCodeAndPersist` calls from `getByCode`, `getById`,
   `getCart(Customer)`, `readableCart`, both `addToCart` overloads, both
   `modifyCart` overloads, `modifyCartMulti`, and `removeShoppingCartItem`
   when it returns a cart.
   The existing store lookup in `getById` is unchanged; only the refresh helper
   is added there.
9. `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`
   (Modify): remove the `promoAdded` one-day check and preserve nulling when no
   discount total exists; do not save from the mapper.
10. `sm-core/src/main/java/com/salesmanager/core/business/services/order/ordertotal/OrderTotalServiceImpl.java`
    (Modify): call `DiscountService` once per summary outside the per-item loop.
11. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java`
    (Modify): keep undiscounted subtotal, expose a positive discount line, and
    subtract the discount exactly once when computing total.
12. `sm-core/src/main/java/com/salesmanager/core/business/configuration/ProcessorsConfiguration.java`
    (Modify): remove `promoCodeCalculatorModule`; the resulting empty list is
    valid and the order-total service still supports future processors.
13. `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java`
    and `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`
    (Delete): remove the promo processor and the rules file outright.
14. `sm-core/src/test/resources/sql/create_schema.sql` (No change needed; it
    only creates the schema and Hibernate's `hbm2ddl.auto=create` generates the
    tables). Create
    `sm-shop/src/test/java/com/salesmanager/test/shop/integration/discount/DiscountApiIntegrationTest.java`
    extending `ServicesTestSupport`, and add discount-cart cases next to the
    existing `ShoppingCartAPIIntegrationTest` using its fixtures. Assert POST
    201, GET 200 with a plain array, PUT 200, DELETE 200 with an empty body,
    invalid input 400, duplicate code 409, missing/cross-store id 404, valid
    apply 201, unknown/cross-store/inactive/out-of-date/below-minimum/no-item
    apply 400, and rejected apply preserving the previous code. Cover category
    descendants, both formulas and rounding, stale clearing, response spelling,
    and exact totals.

### Verification Plan

*   **Build**: Maven tests/build on JDK 21.
*   **Unit**: validation, normalized uniqueness, inclusive dates, minimum based
    on undiscounted subtotal, category lineage, eligible subtotal, amount cap,
    and HALF_UP boundaries.
*   **Integration**: private authorization/statuses; POST/PUT/DELETE response
    shapes; cart apply, rejection-preservation, read recalculation, rename,
    deactivation, deletion, item removal, and cross-store cases.
*   **Regression**: `Test1234` has no effect unless persisted; no discount is
    duplicated per item; existing non-discount totals remain unchanged.

--------------------------------------------------------------------------------

*Drafted with EGM*
