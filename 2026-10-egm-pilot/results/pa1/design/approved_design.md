# Design: merchant-managed discount codes

## Goal and scope

Replace the hard-coded `Test1234` Drools rule with persisted discount codes owned by a
`MerchantStore`. Add the private merchant CRUD API and make the existing cart promo
endpoint validate and apply those codes. Discount state is intentionally recalculated
from the current cart and current discount record whenever a cart is returned; no
discount amount is stored on the cart.

The existing `ShoppingCart.promoCode` column remains the applied-code reference. The
existing `promoAdded` column is no longer used for expiry and may be left in the schema
for compatibility (or deprecated in the Java model). Do not create a migration that
removes it because existing installations use Hibernate schema update.

## Repository placement

Follow the current module split:

- `sm-core-model`: persistent `Discount` entity and `DiscountType` enum.
- `sm-shop-model`: `PersistableDiscount` request/response DTO (including `id`) and,
  if useful for clean service boundaries, a small evaluation/result type.
- `sm-core`: `DiscountRepository`, `DiscountService`, and the shared discount
  eligibility/calculation service. The repository must be store-scoped for every
  lookup.
- `sm-shop`: `DiscountApi` under the existing `/api/v1` controller package, a facade
  if the project’s service/facade convention requires one, and cart integration in the
  existing shopping-cart facade/mapper path.
- Tests should be added at the service and API integration levels following the current
  `sm-shop/src/test` conventions.

## Persistence model

Add a `DISCOUNT` entity with:

- generated `id` using the project’s `TABLE_GEN`/`SM_SEQUENCER` convention;
- mandatory lazy `@ManyToOne MerchantStore merchantStore`;
- `code` as the exact merchant-supplied display value;
- `normalizedCode`, a non-null upper-case `Locale.ROOT` value used for matching;
- enum `type` persisted as `EnumType.STRING` (`PERCENT`, `AMOUNT`);
- `value` as `BigDecimal`, with sufficient precision/scale for currency values;
- nullable `minimumSubtotal`;
- non-null `startDate` and nullable `endDate` as `LocalDate` (or the project’s
  equivalent date mapping);
- non-null `active`, defaulting to `true`;
- a many-to-many association to `Category` through a dedicated join table such as
  `DISCOUNT_CATEGORY`.

Add a database unique constraint/index on `(MERCHANT_ID, NORMALIZED_CODE)`. The
service must still check for conflicts so the API can return a deliberate 409, and must
translate a concurrent constraint violation into the same conflict response. The
store foreign key on the discount-category join must prevent categories from another
store being attached.

Code normalization is `trim` followed by upper-casing with `Locale.ROOT`; reject a
blank code. Preserve the submitted nonblank code in `code`, including its case, so
`promoCode` is displayed as the merchant wrote it. Matching and uniqueness use the
normalized value. Use the same normalization for shopper input, including lookup.

The repository needs methods equivalent to:

- list by store, ordered deterministically (id or code);
- find by id and store;
- find by normalized code and store;
- find an existing normalized code for create and for update excluding the current id.

Fetch categories/products needed by calculation without relying on a closed lazy
collection. Category validation must query each submitted code in the supplied store;
all must exist or the request is 400. Duplicate category codes may be de-duplicated
after normalization.

## DTO and validation contract

Use a request/response DTO rather than exposing the JPA entity. JSON fields are:

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

`id` is output-only. `categories` contains category codes, not ids. In the request DTO,
make `type`, `value`, `minimumSubtotal`, `startDate`, and `endDate` String fields so
Jackson accepts malformed values for service-level validation instead of throwing a
500 before validation. `minimumSubtotal` and `endDate` are nullable; `active` defaults
to true; `startDate` defaults to the current date from an injectable clock. Parse the
two numeric strings to `BigDecimal` and dates strictly as ISO `yyyy-MM-dd`; the
response DTO may expose validated numeric values and ISO date strings in the JSON
shape shown above.

Validate centrally in the service so CRUD and cart application have identical rules:

- code and value are present; type is present and exactly one of the two enum values;
- value is greater than zero; `PERCENT` is at most 100;
- minimum subtotal, when supplied, is non-negative;
- end date, when supplied, is not before start date;
- all category codes exist in the same store.

Return 400 for these validation failures, unknown type/category, malformed dates, or
missing fields. Return 409 when the normalized code already exists in that store.
Do not silently change a merchant’s requested type/value during update; PUT validates
the complete replacement and returns the stored replacement including its id.

## Admin API

Add a controller at `/api/v1`. The security configuration already protects
`/api/v1/private/**`; accept the resolved `MerchantStore` with `?store=` selecting the
store. In every admin method call `authorizationUtils.authenticatedUser()`, then
`authorizationUtils.authorizeUser(user, [SUPERADMIN, ADMIN, ADMIN_RETAILER],
merchantStore)`, using the project constants/stream form used by other private APIs.
Every service call must use that resolved store and never trust a store id in the body.

Endpoints:

- `POST /api/v1/private/discounts`: validate, enforce store-local normalized
  uniqueness, persist, and return the stored DTO with HTTP 201 and its `id`.
- `GET /api/v1/private/discounts`: return all codes for the resolved store only.
- `PUT /api/v1/private/discounts/{id}`: load by id plus store, replace all mutable
  fields, validate uniqueness excluding that id, and return the stored DTO. A missing
  id is 404; an id belonging to another store must behave as not found.
- `DELETE /api/v1/private/discounts/{id}`: delete only a code belonging to the
  resolved store. Return HTTP 200 with no body, matching `CategoryApi`; a missing or
  foreign id is 404.

Use the project’s JSON error shape. Add `ConflictException` in
`com.salesmanager.shop.store.api.exception` and a `RestErrorHandler` handler returning
409. Translate duplicate-code checks and `DataIntegrityViolationException` from the
unique constraint to it. Reuse `ResourceNotFoundException` for missing/foreign ids
(404), and use the existing `RestApiException` for validation and inapplicable-code
failures (400). Avoid converting these cases to 503/500.

To prevent Jackson parse failures from reaching the catch-all 500 handler, make
`PersistableDiscount.type`, `value`, `minimumSubtotal`, `startDate`, and `endDate`
String fields. Parse the enum, both numeric values, and strict ISO `yyyy-MM-dd` dates
centrally in the service; malformed values become `RestApiException`/400. The
builder must not leave `HttpMessageNotReadableException` or `InvalidFormatException`
mapped to 500. Response DTO fields may emit the validated stored values in the normal
numeric/date JSON shape.

## Shared eligibility and calculation

Implement one transactional/read-only service operation conceptually shaped like:

`evaluate(cart, requestedOrStoredCode, store, today) -> applicable, canonicalCode,
eligibleSubtotal, discountAmount, reason`.

It must:

1. Resolve the discount by normalized code and the cart’s store. A missing code,
   wrong store, inactive code, or date outside the inclusive `[startDate, endDate]`
   interval is not applicable. A null end date means no upper bound.
2. Compute the cart’s item subtotal before this discount using the same per-line amount
   as the order-total pipeline: `ShoppingCartItem.itemPrice` (the final unit price
   populated by the cart/order calculation) multiplied by `quantity`, exactly as
   `OrderServiceImpl.caculateOrder` computes `st`. The minimum-subtotal test uses this
   full cart subtotal, not the eligible-only subtotal.
3. Determine eligible lines. With no categories every line is eligible. Otherwise a
   product is eligible when any of its categories is one of the configured categories
   or a descendant of one. Resolve category codes within the cart’s store using
   case-sensitive matching, as category codes are matched elsewhere. `Category.lineage`
   is stored like `/1/5/12/` and includes the category’s own id. An item is eligible
   when any product category has a lineage containing `/<configuredCategoryId>/`.
   Do not compare category display names, and restrict product/category data to the
   cart’s store.
4. Require at least one eligible item. Sum eligible line subtotals.
5. For `PERCENT`, calculate eligible subtotal × value / 100. For `AMOUNT`, use the
   lesser of value and eligible subtotal. Round the final discount once to scale 2
   using `RoundingMode.HALF_UP`; never return a negative value or a discount above
   eligible subtotal after rounding.

Use `BigDecimal` throughout; do not use the current Drools `Double` percentage path.
Define today as `LocalDate.now(clock)`, with an injectable `java.time.Clock` bean in
the system default zone. Use that clock for both the default `startDate` and
eligibility, and replace it with a fixed clock in tests.

The service should return the persisted canonical code string for display. A shopper
input that differs only by case therefore displays the merchant’s stored spelling.

## Cart application and recalculation

Change `ShoppingCartFacade.modifyCart(cartCode, promo, store, language)` so it loads
the cart, evaluates the requested code against the current cart, and only then stores
the canonical merchant code in `ShoppingCart.promoCode`. If evaluation is not
applicable, throw `RestApiException` before saving anything; the prior promo code
remains unchanged. `ShoppingCartApi.modifyCart` catches that exception and rethrows it
as `ServiceRuntimeException`, which reaches the client as HTTP 400. An unknown cart
continues to throw/rethrow `ResourceNotFoundException` and reaches the client as HTTP
404. Keep the existing successful HTTP 201 status and `ReadableShoppingCart` response
body. A valid application replaces the prior code and leaves the cart with at most one
code. `promoAdded` remains in the entity and may be updated for audit compatibility,
but is unused for validity and expiry.

Centralize cart total calculation so every cart-return path (get by code, add/modify
item, multi-item update, and any cart conversion used by the API) evaluates the
stored promo code again. If it is now missing, inactive, outside dates, below the
minimum, category-ineligible, or has no eligible lines, clear `ShoppingCart.promoCode`
and persist that change, then calculate without a discount. This covers item removal,
discount edits, and discount deletion. It also means a deleted/renamed code cannot
continue to affect an old cart.

Prefer adding a cart-level discount calculation to the order-total pipeline rather
than retaining `PromoCodeCalculatorModule`’s per-product Drools rule. The cart-level
result must create exactly one `OrderTotal` with code `discount`, positive value equal
to the discount, and the canonical code as its text. The order total calculation must
subtract that value exactly once from the final total. For an ordinary cart with no
shipping/tax this yields `total = subtotal - discount`; preserve the project’s existing
shipping/tax behavior while ensuring the discount is not applied to those amounts.

Remove the `PromoCodeCalculatorModule`/`PromoCoupon.drl` path from the active order
total processor configuration (or make the module delegate to the new service if a
configuration compatibility path is required). Delete the `Test1234` rule. No default
discount record is seeded, so `Test1234` has no effect unless an admin creates it.

Update `ReadableShoppingCartMapper` to stop checking `promoAdded` and to use the
calculated totals as the source of truth. When a valid discount exists, set
`promoCode` to the canonical stored code, include one total whose JSON `code` is
`discount` and whose `value` is positive, and expose the recalculated total. When it
does not, set `promoCode` to `null`, as the existing mapper already does at its
no-discount path around line 266, and omit the discount line. Ensure stale totals from
a previous conversion are not reused.

Keep the order-side change minimal: remove the one-day `promoAdded` expiry block in
`OrderServiceImpl` around line 436. Because the new discount is computed inside the
shared order-total pipeline, checkout gets the same amount automatically. Make no
other order-side changes beyond removing the Drools promo path and this expiry logic.

## Error and consistency behavior

- Applying an unknown or inapplicable code is 400 and is atomic with respect to the
  cart’s prior code.
- Applying a code to a cart from another store cannot resolve it and is 400; all admin
  reads/writes are store-scoped and foreign ids are 404.
- A concurrent create/rename race is resolved by the database unique constraint and
  surfaced as 409.
- Deleting a discount does not scan carts. Existing carts drop it lazily on their next
  read/recalculation.
- No discount amount or eligible-item snapshot is persisted, so edits to product
  prices/categories and edits to the code take effect on the next calculation.

## Tests and acceptance checks

The concrete cart-return paths that must recalculate and clear a stale code are:

- `ShoppingCartFacadeImpl.getByCode` for `GET /api/v1/cart/{code}`;
- `ShoppingCartFacadeImpl.addToCart(...)` for `POST /api/v1/cart` when it returns the
  cart;
- `ShoppingCartFacadeImpl.modifyCart(String, PersistableShoppingCartItem, ...)` for
  add/modify item;
- `ShoppingCartFacadeImpl.modifyCartMulti(String, List<...>, ...)` for multi-item;
- `ShoppingCartFacadeImpl.modifyCart(String, String, ...)` for promo application;
- `ShoppingCartFacadeImpl.getCart(Customer, ...)` and customer-cart API paths that
  delegate to it;
- any other facade method returning `ReadableShoppingCart` through
  `ReadableShoppingCartMapper`, which is the final shared recalculation boundary.

The promo endpoint retains HTTP 201 and its existing response body; only an
inapplicable code produces the specified HTTP 400.

Add integration tests for:

- create returns 201/id; list/update/delete are store-scoped; foreign ids are hidden;
- DELETE returns 200 with no body;
- malformed JSON/type/date/numeric values produce 400 rather than the catch-all 500;
- case-insensitive uniqueness within a store, same code allowed in two stores, and
  conflict on rename;
- defaults, strict date validation, all bad type/value/date/category cases;
- active flag, inclusive start/end dates, future/not-yet-active and expired codes;
- minimum subtotal based on the full cart, empty/eligible category behavior, and
  parent/descendant category matching;
- percent and amount calculation, amount cap, 2-decimal HALF_UP boundaries, and
  multiple quantities;
- case-insensitive shopper application, canonical display spelling, replacement of a
  prior code, and invalid application preserving the prior code;
- cart response totals (`discount` positive and total reduced), recalculation after
  item removal, deactivation/edit/delete, and no one-day expiry;
- `Test1234` produces no discount until explicitly created.

Use a fixed clock and prices with fractional cents in service tests. Verify both the
HTTP status/error body and persisted state, not only the response payload.

## Build sequence for the coding agent

1. Add entity/enum, repository, DTOs, and service validation with unit tests.
2. Add the private controller and exception/status mapping with API integration tests.
3. Implement the shared evaluator and replace the Drools promo module in cart/order
   total calculation.
4. Update cart application/retrieval/mapper behavior and add end-to-end recalculation
   tests.
5. Run the relevant Maven module tests and a full Maven build; inspect generated schema
   behavior for H2 and the supported production database profiles.
