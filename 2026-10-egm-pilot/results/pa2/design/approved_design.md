# Design: store-managed discount codes

## Goal and scope

Replace the hard-coded Drools coupon (`Test1234`) with persisted, store-owned discount codes. Administrators manage codes through `/api/v1/private/discounts`; shoppers apply one through the existing cart promo endpoint. Discount eligibility and amount are recalculated whenever a cart is calculated or serialized, so a code cannot remain effective after its data or the cart changes.

This design is for the existing Maven modules and Spring/JPA conventions in this checkout. It does not add a second promotion system, migrate `Test1234` into data, or change product-price specials. `Test1234` has no effect after this change unless a store explicitly creates it.

## API contract

Add `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountApi.java` with base mapping `/api/v1`:

| Method | Path | Result |
|---|---|---|
| POST | `/private/discounts?store={store}` | `201`, the stored discount including generated `id` |
| GET | `/private/discounts?store={store}` | `200`, all discounts for the resolved store |
| PUT | `/private/discounts/{id}?store={store}` | `200`, the replaced stored discount |
| DELETE | `/private/discounts/{id}?store={store}` | `200` with an empty body |

Use the same authenticated-user and role checks as the existing private v1 administration APIs (at minimum the normal admin/retail administration groups), and use the resolved `MerchantStore` rather than trusting a store supplied in the body. Every read/update/delete must constrain the lookup by both `id` and store; an id from another store must not be exposed or modified. Follow the existing exception handler, mapping validation errors to 400, duplicate codes to 409, and missing store-owned resources to the established 404 behavior.

Use separate request/read DTOs rather than exposing the JPA entity. The JSON shape is:

```json
{
  "id": 12,
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

`id` is response-only. `minimumSubtotal`, `endDate`, and `categories` are optional. On create, `active` defaults to `true` and `startDate` defaults to `LocalDate.now(clock)` using the system-default zone. PUT is a full replacement: apply the same defaults for omitted optional/defaulted fields, and reject a missing required field instead of silently retaining the old value. Preserve `code` exactly as entered for API responses and shopper display; compare a normalized form (at least case-insensitive, using a locale-independent normalization) for uniqueness and lookup. Do not trim or rewrite the merchant's stored spelling without explicitly deciding that as an API change; reject blank/whitespace-only codes.

## Data model and persistence

Add a `DiscountCode` entity in `sm-core-model`, following `MerchantStore` ownership and table-generator conventions used by the other entities. Suggested fields:

- `id` (`Long`), generated with a dedicated `SM_SEQUENCER` key;
- `merchantStore` (`ManyToOne`, non-null);
- `code` (non-null string);
- `normalizedCode` (non-null string used for case-insensitive uniqueness);
- `type` enum `PERCENT`/`AMOUNT`, persisted as a string;
- `value` and optional `minimumSubtotal` as `BigDecimal` with currency-safe precision/scale;
- `startDate` and optional `endDate` as date-only values;
- `active` boolean, defaulting to true;
- a collection of category references, preferably a join table from discount to `Category`.

Store/category references must be validated to belong to the same merchant store. Store ownership should be represented in the entity and enforced in repository queries. Add a database uniqueness constraint on `(MERCHANT_ID, NORMALIZED_CODE)` in addition to service validation; the service must translate a concurrent constraint failure into 409. Add indexes for `(MERCHANT_ID, NORMALIZED_CODE)` and, if useful for lookup, `(MERCHANT_ID, ACTIVE, START_DATE, END_DATE)`.

The schema comes from the JPA mapping: supported profiles use `hibernate.hbm2ddl.auto=update` and tests use `create`. Add the table, sequence entry, join table, indexes, and constraints through the entity mappings. Do not seed `Test1234`.

Add repository methods equivalent to:

- find all by store;
- find one by id and store;
- find one by store and `normalizedCode`;
- save/update and delete.

The application/service layer (`DiscountCodeService` and implementation in `sm-core`) owns validation, defaults, duplicate handling, category resolution, and the single eligibility/calculation operation described below. The shop module facade maps DTOs and converts service exceptions into API responses.

## Validation rules

Validate before persistence:

- code is present and not blank;
- type is exactly a supported enum value; unknown/null type is 400;
- value is present and strictly positive; `PERCENT` is no greater than 100; `AMOUNT` is in the store currency;
- `endDate`, when present, is not before `startDate`;
- every category code exists in the same store; unknown or cross-store category is 400;

Use `BigDecimal` throughout calculation and comparisons. Do not use `double`. Dates are local calendar dates, not timestamps. Register one injectable `Clock` bean using the system-default zone; every default start date and eligibility “today” is `LocalDate.now(clock)`. Do not add store-timezone lookup.

## Eligibility and calculation service

Create one reusable service operation, conceptually:

`DiscountResult evaluate(ShoppingCart cart, MerchantStore store, LocalDate today, String enteredCode)`

It must load the code by the cart's store and normalized code, then reject as ineligible if any condition fails:

1. the code exists and belongs to the cart's store;
2. it is active;
3. `today >= startDate` and, if `endDate` exists, `today <= endDate`;
4. cart subtotal is at least `minimumSubtotal`, treating a missing minimum as zero;
5. at least one cart item is eligible.

An item is eligible for an unrestricted code. For a categorized code, it is eligible when the product is assigned to one of the selected categories or to a descendant of one of them. Resolve descendants using the existing category `parent`/`lineage` model and ensure the product/category associations are loaded before leaving the transaction. Prefer resolving the selected category subtree once per evaluation and testing each product's categories against it; avoid a query per cart item.

The subtotal used for the minimum is the cart's normal item subtotal before this code's discount, matching the cart `subtotal` field. The eligible subtotal is the sum of each eligible item's current final item price multiplied by quantity (including the same price/attribute handling already used by cart totals). `PERCENT` is `eligibleSubtotal * value / 100`; `AMOUNT` is `min(value, eligibleSubtotal)`. Round the final discount to two decimal places with `RoundingMode.HALF_UP` (so halves round up). Never produce a negative discount or a discount larger than eligible subtotal. Return enough information for totals: matched stored code/display spelling, eligible subtotal, and rounded discount.

The service should distinguish “not found/ineligible” from persistence/system failures. Use an `InvalidDiscountException` for a code that does not apply. The shopper endpoint must let that exception reach the API error mapping as HTTP 400, rather than wrapping it in the current catch-all `new ServiceRuntimeException(e)`, and must not mutate the cart until evaluation succeeds.

## Applying a code and cart lifecycle

Change `ShoppingCartFacade.modifyCart(String cartCode, String promo, ...)` and its v1 controller path `/api/v1/cart/{cartCode}/promo/{code}` so it:

1. loads the cart constrained to the requested store;
2. evaluates the candidate code against the current cart;
3. on failure throws the API's 400 exception without saving anything, preserving the previous `promoCode` and all previous cart state;
4. on success stores the merchant's canonical `DiscountCode.code` spelling (not the shopper's casing) and saves the cart; the existing `promoAdded` field may be retained for compatibility but must not participate in validity;
5. returns the recalculated cart.

The successful promo response remains HTTP 201. A successful application replaces any previous code, so there is still only one `ShoppingCart.promoCode`.

Centralize “recalculate and reconcile promo” in the cart calculation/read path. Before producing totals, if a cart has a promo code, evaluate it again against the current cart and current discount record. If it is no longer eligible (including deactivation, edit, deletion, date change, minimum change, category/product change, or no eligible items), clear the persisted `promoCode` and `promoAdded`, save the cart, and calculate without a discount. This makes deletion and edits naturally invalidate existing carts without a bulk cleanup job.

Remove all one-day checks based on `promoAdded` from:

- `ReadableShoppingCartMapper` around line 114;
- `ShoppingCartFacadeImpl` around line 1117 and related cart-return paths;
- `OrderServiceImpl` around line 437 in shopping-cart total preparation;
- `OrderFacadeImpl` around line 253 in checkout/order-total preparation.

The promo record, not its application timestamp, controls validity. All cart-returning routes (GET, add/modify item, multi-item update, promo application, and checkout calculations) must pass through the same reconciliation/calculation path.

The existing `setPromoAdded(new Date())` calls around `ShoppingCartFacadeImpl` lines 666, 768, 934, and 1156 must not be used to re-apply or refresh a code. Item-update paths must preserve only the already reconciled `promoCode`; they must not set a code from an item payload or refresh its age. On a successful explicit promo application, the code is saved only after `evaluate()` succeeds. `promoAdded` may be cleared and retained only as an unused backward-compatible column.

## Totals and response shape

Replace the Drools-backed `PromoCodeCalculatorModule`/`PromoCoupon.drl` behavior with the persisted discount service. Delete `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`, remove its promo rule wiring from `ProcessorsConfiguration`, and remove the promo `KieSession`/Drools path from `PromoCodeCalculatorModule`. The replacement calculation is a cart-level operation: call `evaluate()` once for the cart, producing at most one discount `OrderTotal`, never one discount per item. Do not multiply a Drools factor into each item's price.

Use this fixed total convention throughout cart and checkout: the discount `OrderTotal` has a positive `value`; `OrderServiceImpl` keeps `summary.getSubTotal()` and the cart `subtotal` as the pre-discount item subtotal; the subtotal totals line also remains the pre-discount item subtotal; and the grand total subtracts the positive discount exactly once. Update the aggregation around `OrderServiceImpl` line 293 so it does not subtract the discount from `subTotal`; instead, subtract it when forming the grand total. `OrderFacadeImpl`, `OrderServiceImpl`, and order creation all use this same pipeline, so persisted order totals are exactly the values produced by it.

The public cart discount line must carry the literal code `"discount"`, not `Constants.OT_DISCOUNT_TITLE` (`"order.total.discount"`). Set the `OrderTotal.orderTotalCode` for the promo variation to `"discount"` and ensure `ReadableShoppingCartMapper` copies that literal into `totals[].code`. Update its check around line 263 to look for `"discount"` when deciding whether an applied promo remains; it must no longer look for `Constants.OT_DISCOUNT_TITLE`. The resulting response must have:

- `promoCode`: the stored merchant spelling from the reconciled evaluation while the code applies, otherwise `null` (the existing mapper convention);
- a `totals` item with exactly `code: "discount"` and positive `value` equal to the rounded discount;
- `total = subtotal - discount` (with existing shipping/tax totals still handled according to their established order);
- no discount line when the code is absent or reconciled away.

Ensure the mapper no longer independently decides whether to expose `promoCode` by inspecting `promoAdded`; it should use the reconciled calculation result. Preserve display-currency formatting through the existing pricing service.

Orders created from a cart must use the same evaluated discount and must not revive an expired one-day promo. At checkout, recalculate from current cart/code state before payment/order persistence; do not trust a stale previously returned total. The persisted order totals are the totals produced by this same pipeline.

## Error and concurrency behavior

- Invalid request fields, unsupported type, invalid dates, invalid values, and unknown categories: 400.
- Duplicate normalized code within one store on create or rename: 409, including a database race.
- Missing store-owned `{id}`: existing 404 behavior; never reveal whether another store owns it.
- Shopper code that is unknown, inactive, outside its date range, below minimum, from another store, or has no eligible item: 400; previous cart code remains unchanged.
- Authentication/authorization follows existing private API behavior.

Add `ConflictException` in `sm-shop` with `@ResponseStatus(HttpStatus.CONFLICT)` and add a specific 409 branch/handler in `RestErrorHandler`; translate duplicate service/repository failures to this exception. Add a dedicated validation/ineligible exception handler that returns 400 without dereferencing `getCause()`. Also fix the existing `handleServiceException(ServiceRuntimeException)` and generic `Exception` handler paths to be null-safe when a cause is absent.

Malformed JSON must return 400, never 500. The request DTO must represent `type` as a `String`, not bind it directly to an enum; represent `startDate`/`endDate` as strings and parse them strictly as `yyyy-MM-dd` in the service. Represent `value` and `minimumSubtotal` so non-numeric JSON is caught by a dedicated `HttpMessageNotReadableException` 400 handler. Unknown type, bad date, non-numeric value, and missing required code/value all therefore take the concrete 400 path.

The promo controller must not wrap every exception in `new ServiceRuntimeException(e)`. Let the invalid/ineligible discount exception pass to the dedicated 400 handler; preserve normal mapping for not-found and system failures. Wrap admin create/update/delete in transactions. On PUT, validate the replacement and uniqueness against all other records before saving. On DELETE, a later cart evaluation sees no code and clears any applied code. A cart evaluation should use a consistent transaction/read view so it cannot calculate from a partially updated discount.

## Tests and acceptance coverage

Add focused service, repository/integration, controller, and cart/total tests in the modules where those patterns already exist. At minimum cover:

- create returns 201 and id; list/update/delete are store-scoped;
- case-insensitive duplicate create and rename, including same code in two stores;
- all 400 validation cases, defaults, canonical spelling, and category ownership;
- exact start/end inclusivity, inactive codes, minimum subtotal, empty cart/no eligible item;
- unrestricted, direct-category, descendant-category, and unrelated-category items;
- percentage and amount calculations, amount cap, two-decimal HALF_UP boundaries, quantities, and mixed eligible/ineligible lines;
- case-insensitive shopper application, replacement of an existing code, and preservation of the old code after a failed application;
- every cart-return path recalculates; item removal, code edit/deactivation/deletion, date transition, and category changes clear the code and discount;
- no one-day expiration and no implicit `Test1234` discount;
- cart response has positive `discount`, correct subtotal/total, and no stale discount line;
- checkout/order totals agree with cart totals and discount is applied once.

Run the relevant Maven module tests plus the full repository test suite after implementation. The design is complete when these behaviors are covered without any remaining reference to the hard-coded rule or the one-day promo lifetime.
