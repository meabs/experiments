# Design: merchant-managed discount codes

## Goal and scope

Replace the hard-coded Drools promo (`Test1234`) with persisted, store-owned discount codes. Merchants manage codes through the private v1 API; shoppers apply one code to a cart through the existing cart promo endpoint. The same cart-level calculation must be used whenever a cart is returned and when an order total is calculated.

This is a design only. No code or database migration is included in this draft.

## Existing implementation to replace

- `ShoppingCart` stores `promoCode` and the obsolete `promoAdded` timestamp.
- `ShoppingCartFacadeImpl.modifyCart(String, String, ...)` saves a promo without validating it.
- `OrderServiceImpl.caculateShoppingCart(...)` rejects a promo after one day.
- `PromoCodeCalculatorModule` evaluates `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`; that rule is the only reason `Test1234` works.
- `ReadableShoppingCartMapper` also applies the one-day display filter and gets totals from `ShoppingCartCalculationService`.
- `OrderTotalServiceImpl` invokes post-processors once per item, which is unsuitable for one cart-level AMOUNT discount and can create multiple discount lines.

Keep `ShoppingCart.promoCode` as the merchant-entered/display value for compatibility, but stop using `promoAdded` for validity. The timestamp can remain as a nullable legacy column/property for compatibility with existing data, but no read or calculation path may consult it.

## Persistence model

Add the core entity `com.salesmanager.core.model.order.discount.DiscountCode`:

- `id`: generated Long using the repository's `SM_SEQUENCER` table-generator convention.
- `merchantStore`: required `ManyToOne` to `MerchantStore`.
- `code`: required merchant spelling, nonblank.
- `normalizedCode`: a comparison key produced by `code.toUpperCase(Locale.ROOT)`. Normalize case only; never trim. A missing or blank original `code` is invalid and produces 400.
- `type`: enum `PERCENT` or `AMOUNT` persisted as a string.
- `value`: `BigDecimal`, required.
- `minimumSubtotal`: nullable `BigDecimal`; null means no minimum.
- `startDate`: required `LocalDate`, defaulted by the service to `LocalDate.now(discountClock)`.
- `endDate`: nullable date; null means no upper bound.
- `active`: required boolean, default true.
- category codes: an `@ElementCollection` of strings in a separate `DISCOUNT_CODE_CATEGORY` join table, scoped by the discount ID. Store the merchant-supplied category codes exactly as supplied; validate each code against the requested store's categories on every create/update.

Add a store-scoped unique constraint/index on `(MERCHANT_ID, NORMALIZED_CODE)`. The service must still pre-check and translate a database uniqueness violation to 409, because two concurrent creates/renames can pass a pre-check. Do not make `code` globally unique.

Add a repository and service in `sm-core` following the existing `JpaRepository` and `SalesManagerEntityServiceImpl` patterns. Required operations are:

- list by merchant ID ordered by ID ascending;
- find by merchant ID and normalized code;
- find by merchant ID and ID;
- case-insensitive uniqueness check excluding an ID for PUT;
- save/update/delete.

The service owns validation, store ownership checks, category resolution, uniqueness handling, and mapping between persistence and the API model. A discount loaded by ID must always be fetched with the requested store condition, so an ID from another store is never editable or deletable through this API.

## API model and administration API

Add shop-layer request/response models under the existing discount/model package. They should expose exactly:

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

`id` is present in stored responses, including POST 201. Optional request fields are nullable/omittable. `active` defaults to true and `startDate` defaults to `LocalDate.now(discountClock)`. Define one injectable `Clock discountClock` bean as `Clock.systemDefaultZone()` and inject that same clock into the admin service and cart evaluator; tests replace it with a fixed clock. `endDate == null` means no end date. Do not default `minimumSubtotal` into a misleading nonzero value; treat null as zero for eligibility while preserving null in the response.

Use a request DTO `type` field of type `String`, not the enum, so an unknown JSON value reaches domain validation and becomes `DiscountBadRequestException`/400 instead of failing enum binding. Keep `value`, `minimumSubtotal`, `startDate`, and `endDate` typed as `BigDecimal`/`LocalDate` in the request DTO. Add `RestErrorHandler.handleHttpMessageNotReadable(HttpMessageNotReadableException)` with `@ResponseStatus(HttpStatus.BAD_REQUEST)` for malformed dates, numbers, and other syntactically invalid JSON values. This prevents the current generic `Exception` handler from returning 500. Add API tests for unknown `type`, malformed date, and malformed number, all expecting HTTP 400.

Add a controller such as `DiscountApi` under `com.salesmanager.shop.store.api.v1`, mapped at `/api/v1`:

- `POST /private/discounts?store=...`: authenticate and authorize with the same `UserFacade` pattern and merchant-admin groups used by the other private management endpoints; call `DiscountFacadeImpl.create(...)`, which delegates validation to the core discount service and translates sm-core validation failures to `DiscountBadRequestException`; persist and return the stored DTO with HTTP 201.
- `GET /private/discounts?store=...`: same protection and store resolution; return only that store's codes.
- `PUT /private/discounts/{id}?store=...`: same protection; call `DiscountFacadeImpl.update(...)` to replace all editable fields from the request, retain the ID/store, translate validation failures to `DiscountBadRequestException`, and return the stored code with HTTP 200. A missing ID in this store is 404.
- `DELETE /private/discounts/{id}?store=...`: same protection and ownership check; call `DiscountFacadeImpl.delete(...)`, translate a missing store-owned ID to the existing `ResourceNotFoundException`, and return HTTP 204 with no body.

Use `@Valid` only for structural bean validation that is compatible with the defaults; domain validation belongs in the discount service so `type`, date ranges, categories, and uniqueness have one implementation. Preserve the merchant's `code` spelling in responses and in `ShoppingCart.promoCode`.

Validation and HTTP mapping:

- 400: missing/blank code, missing value, unknown type, value <= 0, PERCENT value > 100, end before start, malformed dates/numbers, or any category code not found in the requested store. The discount service/facade throws `DiscountBadRequestException extends RestApiException` for every domain validation failure in this list; the existing `RestErrorHandler.handleRestApiException(RestApiException)` maps it to 400. If an sm-core service throws a checked `ServiceException` while resolving categories or persisting data, `DiscountFacadeImpl` catches it and translates the domain validation failure to `DiscountBadRequestException` before returning to the controller.
- 409: normalized code already exists in that store, including a PUT rename collision. `DiscountConflictException` extends `RuntimeException`, not `RestApiException`, and is mapped by a dedicated `RestErrorHandler.handleDiscountConflict(...)` method with `@ResponseStatus(HttpStatus.CONFLICT)`. Keeping it outside the `RestApiException` hierarchy makes the 409 mapping unambiguous; the dedicated handler is also the most specific handler for this exception.
- 404: requested discount ID does not exist for the requested store; throw the existing `ResourceNotFoundException`, which `RestErrorHandler.handleServiceException(ResourceNotFoundException)` already maps to 404.
- Authentication/authorization behavior remains the existing private API behavior.

Do not silently uppercase the stored `code`; comparison uses `normalizedCode`, and shopper input is normalized with `toUpperCase(Locale.ROOT)` for lookup without trimming.

## Single cart-level discount evaluator

Introduce the core service `DiscountCalculationService` with two related operations:

1. `evaluate(code, cart, store)` returns either an invalid reason or a value object containing the matched discount, eligible subtotal, and positive two-decimal discount.
2. `refreshCartDiscount(cart, store)` re-evaluates `cart.promoCode`; if it no longer applies, clears `promoCode` and saves the cart in the surrounding transaction; otherwise returns the computed value.

Both methods obtain `today` from the injected `Clock discountClock` with `LocalDate.now(discountClock)`. No caller supplies an independently chosen timezone or date.

The evaluator must enforce all of these in order:

- resolve the code case-insensitively in the cart's store (and verify the cart/store relationship);
- `active == true`;
- `today >= startDate` and (`endDate == null` or `today <= endDate`), inclusive;
- cart subtotal is at least `minimumSubtotal`, with null treated as zero;
- there is at least one eligible cart item.

For category matching, resolve each configured category through `CategoryService.getByCode(store, categoryCode)` at evaluation time. An item is eligible if its product is directly assigned to one resolved category or to any descendant. Use the existing `Category.lineage` (`/<id>/.../`) and `Product.categories` relationship with exact root-lineage prefix/boundary matching, never a loose substring match. A category-less discount makes every cart item eligible. A category code that no longer resolves is ignored. If none of a discount's configured categories resolve, no item is eligible and the discount does not apply.

Use the cart line item price multiplied by quantity for both the cart subtotal and eligible subtotal, consistently with `OrderServiceImpl`. The counted set is exactly the list constructed in `OrderServiceImpl.caculateShoppingCart`: `new ArrayList<>(shoppingCart.getLineItems())` filtered by `p -> p.getProduct().isAvailable()`. Items whose product is not available do not contribute to the subtotal, minimum check, eligible subtotal, or discount. `minimumSubtotal` is checked against the whole available-item cart subtotal, while the discount amount is calculated only from eligible available items.

Calculation:

- `PERCENT`: `eligibleSubtotal * value / 100`.
- `AMOUNT`: `min(value, eligibleSubtotal)`.
- Round the resulting discount once to scale 2 with `RoundingMode.HALF_UP`; never allow it to exceed eligible subtotal or make the total negative.
- The result is a positive `BigDecimal` discount value. The displayed total is `subtotal - discount`.

The evaluator must be the only place that decides whether a stored promo still applies. It must not use `promoAdded`, and it must not mutate the cart when merely testing a new code for the apply endpoint.

## Cart application and refresh behavior

Change the existing `POST /api/v1/cart/{cartCode}/promo/{code}` path through `ShoppingCartFacadeImpl`:

- Load the cart store-scoped.
- Evaluate the requested code against the current cart before changing the entity.
- If invalid, throw `DiscountBadRequestException extends RestApiException`. Do not clear or replace the existing `promoCode`; the response is an error and the prior code remains persisted. In `ShoppingCartApi.modifyCart(String code, String promo, ...)` (the catch block around lines 129-143), rethrow `DiscountBadRequestException` before the existing generic wrapping branch. The existing `RestErrorHandler.handleRestApiException(RestApiException)` maps it to HTTP 400. The endpoint's successful response remains HTTP 201.
- If valid, save the matched discount's stored `code` (the merchant's spelling) into `ShoppingCart.promoCode`, regardless of the case used by the shopper. Never save the shopper's raw path value.
- Set/retain no expiry timestamp; `promoAdded` is irrelevant. Return the recalculated cart with HTTP 201, as the existing successful endpoint does.

At the start of every cart calculation/serialization, call `refreshCartDiscount`. This must cover `GET /cart/{code}`, add/modify/remove item responses, customer-cart reads, and any other path that invokes `ReadableShoppingCartMapper` or `ShoppingCartCalculationService`. If an edited/deactivated/deleted/expired code, changed subtotal, or changed category membership makes the code invalid, clear it before creating the response. The exact JSON result is `"promoCode": null`; `totals` contains no object whose `code` is `"discount"`. A deleted code must therefore be removable without scanning carts.

Do not put refresh/evaluation only in the mapper. `ShoppingCartCalculationServiceImpl.calculate(ShoppingCart, MerchantStore, Language)` continues to delegate to `OrderService`; the single refresh/evaluation is performed by `OrderServiceImpl.caculateShoppingCart(...)` as described below, inside the same calculation transaction. This ensures every cart response that uses the calculation service refreshes the code before mapping and totals are returned.

No path may overwrite `ShoppingCart.promoCode` without going through `DiscountCalculationService.evaluate`. In `ShoppingCartFacadeImpl.updateCartItems(Optional<String> promoCode, ...)` (the current assignments around lines 663-666), only replace the existing code when the optional candidate evaluates successfully; if it is absent or invalid, leave the existing valid code unchanged. In the add-item path assignment around lines 766-768 and the item-modification assignment around lines 932-934, evaluate `item.getPromoCode()` first; set the matched discount's stored merchant spelling only when accepted, and ignore an invalid candidate, retaining any existing code. Do not set `promoAdded` in any of these paths.

Remove these one-day checks explicitly: `OrderFacadeImpl` around lines 251-266; `ShoppingCartFacadeImpl` around lines 1116-1127; `ReadableShoppingCartMapper` around lines 113-124; and the date logic in `OrderServiceImpl.caculateShoppingCart`. Keep `ShoppingCart.promoAdded` and its database column as-is, but never read or write it for discount validity.

Remove `PromoCodeCalculatorModule` from `ProcessorsConfiguration.orderTotalsPostProcessors()` and from `sm-core/src/main/resources/spring/processors/shopizer-core-ordertotal-processors.xml`; delete `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`. No fallback lookup or special case for `Test1234` remains.

## Totals and order integration

Use one direct cart-level calculation in `OrderServiceImpl.caculateShoppingCart(ShoppingCart, Customer, MerchantStore, Language)`. Refactor this method to retain the filtered available `itemList`, compute its base subtotal using `item.getItemPrice().multiply(new BigDecimal(item.getQuantity()))`, call `DiscountCalculationService.refreshCartDiscount(...)` exactly once after that subtotal is available, and pass the resulting evaluation value into `caculateOrder(...)`. The order calculation should then:

1. build the current available cart item list and base subtotal;
2. receive that one `DiscountEvaluation` from `caculateShoppingCart(...)` after the available-item subtotal is established;
3. add at most one `OrderTotal` with `orderTotalCode = Constants.OT_DISCOUNT_CODE` (a new constant whose literal value is `"discount"`), positive `value`, and the applied code as its text; leave `Constants.OT_DISCOUNT_TITLE` as the existing title/module constant (`"order.total.discount"`);
4. subtract that positive value once from the subtotal and `grandTotal` in `caculateOrder`;
5. expose the discount in the returned `OrderTotalSummary` and cart DTO.

`OrderTotalServiceImpl.findOrderTotalVariation(...)` must no longer produce any discount line per item; with `PromoCodeCalculatorModule` removed from `ProcessorsConfiguration.orderTotalsPostProcessors()` and `sm-core/src/main/resources/spring/processors/shopizer-core-ordertotal-processors.xml`, it only handles the remaining post-processors. The discount line is created directly by `OrderServiceImpl.caculateOrder(...)`, once per cart calculation, with `orderTotalCode = Constants.OT_DISCOUNT_CODE` and the existing subtotal-level sort order. `OrderServiceImpl.caculateShoppingCart(...)` is the only caller that invokes the discount evaluator for a cart.

Update `ReadableShoppingCartMapper` so it derives `promoCode` from the refreshed valid cart state, not from a timestamp. Map the discount line with `code: Constants.OT_DISCOUNT_CODE`, whose literal JSON value is exactly `"discount"`, and its positive value. Change the existing no-discount check around mapper lines 262-267 to compare `t.getOrderTotalCode()` with `Constants.OT_DISCOUNT_CODE`, not `Constants.OT_DISCOUNT_TITLE`. `ReadableShoppingCart.total` is set from `OrderTotalSummary.getTotal()`, which is the `grandTotal` after the single discount subtraction (plus existing shipping/tax behavior). When no code applies, emit `promoCode: null` and omit the discount line from `totals`.

Use the same discount value in checkout/order summary calculation so a cart cannot display one amount and charge another. Confirm the existing order flow copies `shoppingCart.getPromoCode()` and does not reintroduce the removed expiry rule.

## Database/schema considerations

This checkout uses Hibernate `hbm2ddl.auto=update` for normal profiles and `create` in tests. Map the entity to `DISCOUNT_CODE` and its element collection to `DISCOUNT_CODE_CATEGORY`; Hibernate creates/updates these tables in the repository's configured environments. Do not modify existing cart rows; old `Test1234` values must simply stop resolving and be cleared on their next calculation. Keep `ShoppingCart.promoAdded` as-is but unused.

## Tests

Add unit tests for the evaluator and service, plus API/integration coverage following the existing `sm-shop` integration-test style:

- POST returns 201 and an ID; GET is store-scoped; PUT replaces fields; DELETE removes; cross-store ID access is 404.
- Defaults: active true, start today, null minimum, null end date.
- PERCENT boundaries (0 rejected, 100 accepted, >100 rejected), AMOUNT boundaries, missing fields, unknown type, reversed dates, unknown category, and 409 create/rename collisions ignoring case.
- Same normalized code is allowed in different stores; merchant spelling is preserved.
- Shopper matching ignores case; an invalid code returns 400 and leaves a prior valid cart code unchanged; a valid code replaces the prior one.
- Active/date/minimum checks are inclusive where specified; no end date remains open-ended; no one-day expiry occurs.
- No-category discount includes all items; category discount includes direct and descendant categories but excludes unrelated categories; a product with multiple categories is eligible if any matches.
- Minimum uses whole-cart subtotal, while percentage/amount uses eligible subtotal; amount is capped; half-cent values round HALF_UP to two decimals.
- Returned cart has exactly one positive total whose `code == "discount"` (from the new `Constants.OT_DISCOUNT_CODE`), merchant-written `promoCode`, and subtotal-minus-discount total.
- Removing items, changing quantities, deactivating/editing/deleting a code, or changing category data causes the next returned cart to drop the promo and discount line.
- `Test1234` is rejected unless explicitly created by that store, and then follows normal validation/rules.
- Verify checkout/order totals use the same discount and do not duplicate it per line item.

## Implementation sequence

1. Add the core entity, category collection mapping, repository, service, validation, and conflict/not-found domain errors.
2. Add shop request/response models, mapper/facade methods, and the protected administration controller.
3. Add the cart-level evaluator and wire refresh into the calculation boundary.
4. Rework the existing promo endpoint to validate-before-mutate and replace the old expiry behavior.
5. Replace the Drools/per-item total integration and update cart/order mappers.
6. Run module/integration tests on JDK 21.
