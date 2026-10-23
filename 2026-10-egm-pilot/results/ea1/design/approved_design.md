# Merchant-Managed Discount Codes

*   **Author:** Codex
*   **Status:** Draft
*   **Date:** 2026-10-23

## Overview

Shopizer currently treats a promo code as an input string on `ShoppingCart` and
lets `PromoCodeCalculatorModule` run the Drools rule file
`sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`.
That file contains the expired `Test1234` rule, so merchants cannot manage
codes and the calculation cannot use store, date, subtotal, category, or active
state.

This feature replaces that rule-driven path with persisted, store-owned
discount records and a service that validates and calculates them. Store
administrators manage records through a protected `/api/v1/private/discounts`
resource scoped by `?store=`. Shoppers continue to use
`ShoppingCartApi.modifyCart(String code, String promo, MerchantStore store,
Language language)` through `POST /api/v1/cart/{cartCode}/promo/{code}`.
The cart response produced by `ReadableShoppingCartMapper` will expose the
merchant-written code, a non-negative `discount` total, and a reduced total.

The calculation is performed again whenever the cart is read through the
mapper's single `shoppingCartCalculationService.calculate` call.
`ShoppingCartFacadeImpl.getByCode` performs no calculation of its own. If the persisted code
no longer applies, only the cart's promo state is cleared: `promoCode` becomes
empty and the discount total is omitted. The cart and all of its items remain
unchanged. An invalid replacement attempt is rejected before changing the
stored cart code, so a previously applied code remains in place when a new
promo input is rejected with HTTP 400.

## The Problem

The current implementation has four user-visible defects:

1. `PromoCodeCalculatorModule` can only obtain a percentage from the hard-coded
   Drools rule and does not represent an administrator-owned discount model.
2. `ShoppingCartFacadeImpl.modifyCart(String, String, MerchantStore, Language)`
   saves any supplied string without checking that it belongs to the cart's
   store or is currently usable. The read path and
   `ReadableShoppingCartMapper` additionally expire a code one day after
   `ShoppingCart.promoAdded`, which conflicts with date-based campaign rules.
3. There is no private admin CRUD API, persistent schema, or case-insensitive
   per-store uniqueness constraint for codes.
4. The existing total calculation cannot limit a discount to a category
   subtree, enforce a minimum subtotal, cap fixed-amount discounts, or apply
   `RoundingMode.HALF_UP` at two decimal places.

The replacement must make discount validity a function of the saved discount,
the cart's store and current contents, and today's date. It must remove the
`Test1234` rule entirely: that text has no effect unless an administrator
creates a matching record.

## Goals

* Add a persisted discount model with `id`, store, code, `PERCENT`/`AMOUNT`
  type, value, optional minimum subtotal, start/end dates, optional category
  codes, and active state (defaulting active and start date to today).
* Enforce case-insensitive uniqueness within one store at the database and
  service/API boundaries while allowing the same code in different stores. A
  duplicate on create, or a `PUT` rename to another existing code (compared
  ignoring case), returns HTTP 409. A `PUT` that keeps the record's own name,
  including a case-only change, is not a conflict.
* Provide protected admin CRUD at `POST/GET/PUT/DELETE
  /api/v1/private/discounts[/{id}]`, always resolving and authorizing the
  merchant store from `?store=`. An ID that does not exist, or exists for a
  different store, returns HTTP 404 on `PUT`/`DELETE`; no store can read,
  change, or delete another store's codes.
* Map invalid input to HTTP 400 (missing/invalid fields, dates, type, category,
  or an unusable shopper code), duplicate code to HTTP 409, and preserve the
  old cart code when an apply request is rejected. Every non-applying shopper
  code is HTTP 400, including unknown code, another store's code, inactive
  code, dates outside the validity window, a subtotal below minimum, and no
  eligible items.
* Recalculate a stored code on every cart response. Apply it only when active,
  in date range (inclusive), store-matched, above minimum subtotal, and backed
  by at least one eligible item; traverse category descendants for category
  restrictions; cap `AMOUNT` at eligible subtotal; and round the final discount
  to two decimal places with `HALF_UP`. “Today” is the server-local
  `LocalDate.now()` value, used consistently for defaulting and both inclusive
  start/end comparisons.
* Return `promoCode` as written by the merchant, a non-negative `discount` line in
  `ReadableOrderTotal`/`totals`, and `total = subtotal - discount` when no
  shipping, handling, or tax is present; remove both
  code and line when a later cart/code change makes the discount inapplicable.
* Remove the one-day `promoAdded` expiry checks from
  `ShoppingCartFacadeImpl`, `ReadableShoppingCartMapper`, and order total
  handling, and stop loading `PromoCoupon.drl` for this feature.

## Non-Goals

* No stacking or ordering of multiple codes: a cart stores and applies at most
  one code.
* No customer-specific, usage-count, coupon-redemption, scheduling, or
  reporting features beyond the supplied dates and active flag.
* No change to product sale-price calculation; the discount operates on the
  cart's eligible-item subtotal after normal pricing.
* No migration of historical orders into discount records and no preservation
  of `Test1234` behavior unless a merchant explicitly creates that code.
* No schema migration/backfill/rollback work: these are new tables and the
  repository uses Hibernate `hbm2ddl.auto` for schema creation.
* No pagination, record limits, or bulk category prefetch for the admin list.
* No clock abstraction or timezone configuration; server-local
  `LocalDate.now()` is the rule.
* No optimistic locking or concurrency control for apply versus edits; last
  write wins and the next cart read recalculates the current discount.

## Technical Plan (Architecture)

### Persistence and store isolation

* Create `com.salesmanager.core.model.discount.DiscountCode` in
  `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountCode.java`.
  Map it as `DISCOUNT_CODE` with a generated `DISCOUNT_CODE_ID`, a mandatory
  `MERCHANT_ID` association to `MerchantStore`, merchant-written `CODE`, enum
  `TYPE` (`PERCENT` or `AMOUNT`), decimal `VALUE`, optional decimal
  `MINIMUM_SUBTOTAL`, `START_DATE`, optional `END_DATE`, and `ACTIVE`.
  Map categories as an owning `@ElementCollection Set<String> categories` with
  `@CollectionTable(name="DISCOUNT_CODE_CATEGORY",
  joinColumns=@JoinColumn(name="DISCOUNT_CODE_ID"))` and
  `@Column(name="CATEGORY_CODE")`. PUT clears and repopulates this set in
  place; deleting the entity removes its element-collection rows through JPA.
* Use `@ManyToOne(fetch=FetchType.LAZY, optional=false)` with a non-null
  `MERCHANT_ID` join and no cascade. Copy `Category` exactly for the ID:
  `@TableGenerator(name="TABLE_GEN", table="SM_SEQUENCER", pkColumnName="SEQ_NAME", valueColumnName="SEQ_COUNT", pkColumnValue="DISCOUNT_CODE_SEQ_NEXT_VAL")`
  with `@GeneratedValue(strategy=GenerationType.TABLE, generator="TABLE_GEN")`.
  `CODE` and `CODE_NORMALIZED`
  are `VARCHAR(100)`; `VALUE` and `MINIMUM_SUBTOTAL` are `DECIMAL(19,4)`.
  Do not add a Flyway migration: this repository's runtime profiles use
  `hibernate.hbm2ddl.auto=update` and tests use `create`. Put the schema in the
  JPA mapping. `DiscountCode` stores both merchant-written `CODE` and an
  application-maintained upper-case `CODE_NORMALIZED`, with a
  `@Table(uniqueConstraints = @UniqueConstraint(columnNames =
  {"MERCHANT_ID", "CODE_NORMALIZED"}))`; Hibernate creates that constraint
  for both runtime and test databases. `DiscountCodeServiceImpl` checks the
  normalized value before save and translates a race-induced
  `DataIntegrityViolationException` only to core
  `DiscountCodeConflictException`; `DiscountCodeFacadeImpl` translates that
  core outcome to the shop `DiscountConflictException` and HTTP 409.
* Add `DiscountCodeRepository` under
  `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/`.
  It must provide `findByMerchantStoreOrderByIdAsc(MerchantStore store)`,
  `findByIdAndStore`, `findByStoreAndCodeIgnoreCase`, and an existence query for create/rename that
  excludes the current ID. No repository method used by the admin API may
  query by ID without the store predicate.
* Add `DiscountCodeService` and `DiscountCodeServiceImpl` under
  `sm-core/src/main/java/com/salesmanager/core/business/services/discount/`.
  These classes accept only `DiscountCode` entities and `MerchantStore`; they
  never import `sm-shop-model` DTOs or HTTP exceptions. They perform
  store-qualified CRUD and normalized uniqueness checks and signal core
  outcomes with `DiscountCodeNotFoundException` and
  `DiscountCodeConflictException` in
  `sm-core-model/src/main/java/com/salesmanager/core/business/exception/`,
  beside the existing `ServiceException`. DTO validation, category resolution, and
  defaults are deliberately owned by the shop facade described below.

### Admin API and DTOs

* Add `DiscountCodeApi` at
  `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountCodeApi.java`.
  Implement `POST /api/v1/private/discounts` with `201` and a
  `ReadableDiscountCode`, `GET` with `200` and an id-ascending JSON array
  (no pagination), `PUT /api/v1/private/discounts/{id}` with `200` and the
  updated `ReadableDiscountCode`, and `DELETE` with `200` and an empty body,
  matching `CategoryApi.delete`. There is no item GET endpoint; after DELETE
  the code is absent from collection GET, while PUT or DELETE on that ID is
  404.
  Follow `CategoryApi` with its `AuthorizationUtils` usage and the
  `CustomerApi`/`CustomerFacade`/`CustomerFacadeImpl` controller-facade pattern. The
  `MerchantStoreArgumentResolver` calls `userFacade.authorizeStore(store,
  requestURI)` for every `/private/` path. Absent `?store=` defaults to
  `DEFAULT`; unknown stores become
  `ResourceNotFoundException`, and access is allowed only when the user's
  merchant matches `?store=` or the user is in `GROUP_SUPERADMIN`. Inside every
  method, call
  `AuthorizationUtils.authorizeUser(authorizationUtils.authenticatedUser(),
  Stream.of(Constants.GROUP_SUPERADMIN, Constants.GROUP_ADMIN,
  Constants.GROUP_ADMIN_CATALOGUE, Constants.GROUP_ADMIN_RETAIL).collect(Collectors.toList()),
  merchantStore)`. This checks both group membership and store membership for
  non-superadmins; superadmins may manage any store's codes. Never trust a
  store value in the request body. A null, empty, or blank `categories` list is
  stored as no category restriction.
* Add `PersistableDiscountCode` and `ReadableDiscountCode` in
  `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/`. DTOs
  expose exactly `code`, `type`, `value`, `minimumSubtotal`, `startDate`,
  `endDate`, `categories`, `active`, with `id` on responses. Use ISO
  `LocalDate` strings and `BigDecimal` values; make `type` a `String` in the
  persistable DTO so an unknown value cannot fail Jackson enum binding into a
  500. `DiscountCodeFacadeImpl` validates the string and maps it to `PERCENT`
  or `AMOUNT`, and maps JSON/date/number binding errors to the same HTTP 400
  validation response. Inside `DiscountCodeApi`, controller-local
  `@ExceptionHandler` methods handle `HttpMessageNotReadableException` and
  `MethodArgumentTypeMismatchException`. They return `ErrorEntity`, with
  fields `errorCode` and `message`, matching `RestErrorHandler`. Spring checks
  these handlers before any controller advice; each sets HTTP 400,
  `errorCode = "400"`, and `message = exception.getMessage()`. `code` is
  required, non-blank, at most 100 characters,
  and stored exactly as written without trimming. `value` is required and
  greater than zero; `PERCENT` is at most 100. Optional `minimumSubtotal` must
  be at least zero when present. Persist `value` and `minimumSubtotal` as
  `DECIMAL(19,4)` without an extra scale rule. A null/empty `categories` list
  means no restriction; blank or unknown entries return 400 and duplicate
  entries collapse in the Set. PUT is full replacement: omitted optional
  fields become null or their create defaults (`active=true`,
  `startDate=LocalDate.now()`). If `endDate` is supplied without `startDate`,
  compare it with today and reject an end date before that effective start date.
  Do not silently trim or change the merchant-written response code.
* Extend `RestErrorHandler` with handlers for `DiscountValidationException`
  (400) and `DiscountConflictException` (409). Keep
  `ResourceNotFoundException` (404) for missing/foreign IDs. Shopper
  application failures use the same validation exception, so unknown,
  foreign-store, inactive, out-of-date, below-minimum, and no-eligible-item
  cases all return 400. The controller-local handlers cover malformed JSON,
  null or missing bodies, bad dates/numbers, and non-numeric IDs only on this
  API; other APIs retain the existing generic behavior.
* Add `DiscountCodeFacade` and `DiscountCodeFacadeImpl` under
  `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/`.
  Following the existing `CustomerFacade`/`CustomerFacadeImpl` and
  `CategoryFacade`/`CategoryFacadeImpl` bridge pattern, this layer maps
  `PersistableDiscountCode`/`ReadableDiscountCode` to and from the core
  `DiscountCode` entity, applies `active=true` and `startDate=LocalDate.now()`
  defaults, validates DTO strings/ranges/dates and category codes, and calls
  only the core `DiscountCodeService`. Translate core
  `DiscountCodeNotFoundException` to shop `ResourceNotFoundException` (404),
  `DiscountCodeConflictException` to `DiscountConflictException` (409), and
  facade validation failures to `DiscountValidationException` (400). `DiscountCodeApi`
  calls this facade and never calls the core service directly. Category codes
  are stored and matched exactly as supplied through
  `CategoryService.getByCode(store, code)`; only exactly equal duplicates
  collapse in the `Set`.

### Applying and recalculating a discount

* Add `DiscountCalculationService` in
  `sm-core/src/main/java/com/salesmanager/core/business/services/discount/`.
  Its evaluation method is
  `evaluate(MerchantStore store, String code, List<ShoppingCartItem> pricedItems,
  LocalDate today)`. It loads the code by `CODE_NORMALIZED` using
  `promo.toUpperCase(Locale.ROOT)` for that store,
  checks active and inclusive start/end dates, minimum subtotal, and category
  eligibility, then returns a core-only `DiscountApplicationResult` containing
  only `applicable`, the stored merchant-written code, eligible subtotal, and
  rounded discount amount. `OrderServiceImpl.caculateOrder` alone computes
  order totals. It never throws an HTTP-specific exception for a
  non-applying code; unknown, foreign-store, inactive, date-invalid,
  below-minimum, and no-eligible-item cases are represented as
  `applicable=false`. If `code` is null or blank, return
  `DiscountApplicationResult.notApplicable()` before normalization or any
  lookup. `caculateShoppingCart` does not save the cart or add a discount line
  for this no-code path; it clears and saves only when a non-blank saved code
  fails to apply. The apply endpoint treats a blank promo as HTTP 400 before
  evaluation.
  Resolve each category code with `CategoryService.getByCode(store, code)`.
  Category lineage is stored with slash-delimited IDs (`/id/` for a root and
  parent lineage plus `/<id>/` for descendants, as built by
  `CategoryServiceImpl`). A product may belong to several categories; an item
  is eligible when any one of those product categories equals a selected
  category ID or its lineage contains `/<selectedId>/`. If a saved category
  code no longer resolves, skip that restriction code without failing the
  cart calculation. If categories are configured and none resolve, no item is
  eligible and the discount does not apply. Use one mandatory store-qualified
  JPQL query on `DiscountCodeRepository` per evaluation, selecting product ID,
  category ID, and lineage for the filtered item product IDs. `ShoppingCartItem.product`
  is transient; a product with no rows has no categories, and null products have
  already been removed by the availability filter. Use each
  `ShoppingCartItem`'s already-computed line subtotal (item price × quantity),
  never re-price inside this service. Use `BigDecimal` and
  `setScale(2, RoundingMode.HALF_UP)`. For `PERCENT`,
  multiply eligible subtotal by value, divide by 100 at full precision, then
  round once; do not round the intermediate value/100. For `AMOUNT`, use
  `min(value, eligibleSubtotal)` before rounding. An empty category list means
  every item is eligible. The returned code is always the stored merchant
  `CODE`, never the shopper's casing or spelling. Applicability does not
  require a non-zero discount: if rounding produces `0.00`, retain the code
  and emit a `discount` line with `0.00`; the line is never negative.
* Change `ShoppingCartFacadeImpl.modifyCart(String cartCode, String promo,
  MerchantStore store, Language language)` to evaluate the candidate before
  saving. If `DiscountApplicationResult.applicable` is false, throw the shop
  `DiscountValidationException` without modifying `ShoppingCart.promoCode` or
  `promoAdded`; on success save the evaluator's canonical stored `CODE`, not
  the shopper's input casing (one code maximum). Obtain the same
  unavailable-filtered, priced items through
  `OrderService.preparePricedAvailableItems(cart)`;
  `OrderServiceImpl.caculateShoppingCart` uses that public method internally,
  so there is one pricing path. The existing `ShoppingCartApi` endpoint remains the shopper
  entry point. Its
  current catch block rethrows `ResourceNotFoundException` but wraps every
  other exception in `ServiceRuntimeException`, which the existing
  `RestErrorHandler` maps to 400; the new `DiscountValidationException` must
  be rethrown explicitly so its 400 mapping and message are preserved.
* Use the same item set and prices as the displayed cart subtotal. In
  `OrderServiceImpl.caculateShoppingCart`, obtain the shared
  `preparePricedAvailableItems(cart)` result, put those items in
  `OrderSummary.products`, and compute their line subtotals once with the
  shared `calculatePriceQuantity` helper in `caculateOrder`; set
  `orderSummary.setPromoCode(cart.getPromoCode())` before
  calling it. `caculateOrder` keeps its existing signature and, after line
  subtotals are established, calls `DiscountCalculationService.evaluate(...)`
  once whenever `OrderSummary.getPromoCode()` is non-blank. Ordinary order
  summaries with no promo code receive no discount result. Checkout continues
  to pass the cart code into `OrderSummary` as today, without the removed
  expiry check, so cart and checkout use the same path. `caculateShoppingCart`
  returns the one summary produced by `caculateOrder`; if a non-blank cart code
  yielded no `discount` line, it clears and saves the cart code before
  returning, without a second calculation. The minimum check uses the whole
  filtered, priced cart subtotal, not the eligible subtotal: with shoes at 60
  and hats at 50, a shoes-only discount code with minimum 100 applies because
  110 >= 100, then calculates its discount on 60. This avoids the old per-item
  `pricingService.calculateProductPrice` path and makes both subtotals use the
  displayed prices.
* In `OrderServiceImpl.caculateOrder`, leave existing
  `OrderTotalVariation` modules unchanged: they continue adjusting
  `subTotal` exactly as today. Eligibility and eligible subtotal use the
  priced item line subtotals before those variation
  adjustments. The merchant discount is never routed through the variation or
  post-processor list. Cap it so it never exceeds the resulting summary
  `subTotal`, compute `discount = min(computedDiscount, max(subTotal, 0))`,
  then add one non-negative `OrderTotal` with
  `setOrderTotalCode("discount")` (set explicitly; do not reuse
  `Constants.OT_DISCOUNT_TITLE`, whose value is `order.total.discount`). Set
  the invariant `OrderTotalSummary.total = OrderTotalSummary.subTotal -
  merchantDiscount + shipping + handling + tax`; do not subtract the merchant discount
  from the stored `subTotal`. With no other variations, shipping, or tax, this
  is exactly `total = subtotal - discount`. The full formula is
  `total = max(subTotal - discount + shipping + handling + tax, 0)`. Tax stays on the existing tax
  module's base, unchanged by this feature. The discount is never negative,
  never exceeds post-variation `subTotal`, and the resulting total is never
  negative; legacy variations otherwise run in their existing order and
  behavior. Carry the canonical
  code in a new `OrderTotalSummary.promoCode` field.
  Update `ReadableOrderTotalMapper`'s discounted check to recognize
  `discount`. `Constants.OT_DISCOUNT_TITLE` is also used by
  `ManufacturerShippingCodeOrderTotalModuleImpl`; leave that unrelated module
  and constant unchanged, but do not use the constant for merchant promo
  totals. The mapper must recognize both legacy module output and the new exact
  `discount` code while the new cart promo line is always `discount`.
* `PromoCodeCalculatorModule` is removed from the post-processor list and its
  Drools calculation is deleted; the one cart-level call above is the only
  discount calculation. `ShoppingCartCalculationServiceImpl` continues to
  call `OrderServiceImpl.caculateShoppingCart`, so this covers cart reads,
  adds, item changes, and order totals.
* `ReadableShoppingCartMapper.merge` already calls
  `shoppingCartCalculationService.calculate` and clears `promoCode` when no
  discount line exists. Remove its `promoAdded` expiry copy and make it set
  `promoCode` only from `OrderTotalSummary.promoCode` when a `discount` line
  exists; otherwise leave it empty. Remove the separate
  expiry copy in `ShoppingCartFacadeImpl.getByCode`; that
  method must rely on the mapper result. When a saved code no longer applies,
  `OrderServiceImpl.caculateShoppingCart` clears `ShoppingCart.promoCode` and
  calls `shoppingCartService.saveOrUpdate` after `caculateOrder` returns. The
  evaluator never saves inside its read-only transaction; the existing
  transactional `shoppingCartService.saveOrUpdate` owns the write. The cleared value is persisted, so fixing the
  discount later does not resurrect it.
* Every other setter is handled explicitly: in
  `ShoppingCartFacadeImpl.updateCartItems`, ignore the optional `promoCode`
  argument; in `addToCart` and `readableShoppingCart`, ignore
  `PersistableShoppingCartItem.promoCode` instead of copying it. Callers must
  use the promo endpoint. `ShoppingCartFacadeImpl.modifyCart` remains the sole
  cart-code setter and always invokes the same candidate validation before
  saving. The mapper's `merge` response setters are reduced to the single
  successful-calculation assignment or the empty
  value when the calculation has no discount.

### Removing the old rule and expiry

* Delete `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl`
  and remove the Java processor registration from
  `ProcessorsConfiguration.orderTotalsPostProcessors()` as described above.
  The XML processor file is unchanged because its registration is already
  commented out. Replace the old contribution with the discount calculation
  result described above.
* Remove all `promoAdded` one-day checks from
  `ShoppingCartFacadeImpl.getByCode`, `ReadableShoppingCartMapper`,
  `OrderFacadeImpl`, and `OrderServiceImpl`. Keep the legacy column only as
  inert compatibility data unless a follow-up migration removes it.

## Alternatives Considered

### Keep Drools and add database facts

* **Pros**: Reuses the current `PromoCodeCalculatorModule` hook.
* **Cons**: Per-item Drools execution does not naturally provide one
  cart-level eligible subtotal, category subtree traversal, or exact totals
  semantics, and it preserves the hard-coded rule path.
* **Reason for Rejection**: A dedicated service called once from the existing
  cart calculation has clearer store scoping, validation, rounding, and
  recalculation behavior.

### Store the full discount definition on `ShoppingCart`

* **Pros**: Cart reads would not need a discount lookup.
* **Cons**: Merchant edits/deletes would not reliably affect existing carts,
  and duplicated definitions would break per-store uniqueness and admin CRUD.
* **Reason for Rejection**: Store only the applied code and resolve the current
  definition on every calculation so changes invalidate carts immediately.

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountCode.java` (Create)

* Map the `DiscountCode` JPA entity to `DISCOUNT_CODE`, including the
  `MerchantStore` relationship, merchant-written `code`, `codeNormalized`,
  type, `BigDecimal` value/minimum, `LocalDate` start/end, active flag, and
  `@ElementCollection Set<String> categories` owned by the entity, using
  `@CollectionTable(name="DISCOUNT_CODE_CATEGORY",
  joinColumns=@JoinColumn(name="DISCOUNT_CODE_ID"))` and
  `@Column(name="CATEGORY_CODE")`. A PUT clears and repopulates the set in
  place; deleting the entity lets JPA remove its element-collection rows. Set
  `codeNormalized` from
  `code.toUpperCase(Locale.ROOT)` in `@PrePersist` and `@PreUpdate` callbacks.
  Add the JPA `@UniqueConstraint` on `MERCHANT_ID,CODE_NORMALIZED`; blank
  codes are not normalized into a valid record.

#### 2. `sm-core-model/src/main/java/com/salesmanager/core/model/discount/DiscountType.java` (Create)

* Define only `PERCENT` and `AMOUNT`. The API DTO remains a string so unknown
  JSON values are reported as 400 by service validation rather than Jackson's
  global enum-binding path.

#### 3. `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/DiscountCodeRepository.java` (Create)

* Extend `JpaRepository<DiscountCode, Long>` with store-qualified queries:
  `List<DiscountCode> findByMerchantStoreOrderByIdAsc(MerchantStore store)`,
  find by ID and store, find by normalized code and store, an existence query
  for normalized code excluding an ID, and
  `findProductCategoryRowsByStoreAndProductIds` implementing the JPQL product,
  category ID, and lineage projection. Define interface projection
  `ProductCategoryRow { Long getProductId(); Long getCategoryId(); String getLineage(); }`.
  Its query is
  `@Query("select p.id as productId, c.id as categoryId, c.lineage as lineage from Product p join p.categories c where p.id in :productIds and p.merchantStore.id = :storeId")`
  with `@Param("storeId") Integer storeId` and
  `@Param("productIds") Collection<Long> productIds`. Do not
  expose an admin lookup that can return another store's row.

#### 4. `sm-core-model/src/main/java/com/salesmanager/core/business/exception/DiscountCodeNotFoundException.java` and `DiscountCodeConflictException.java` (Create)

* Add core checked outcomes beside `ServiceException`; they carry no HTTP
  status and can be consumed by `sm-shop` without making `sm-core` depend on
  shop packages.

#### 5. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountCodeService.java` and `DiscountCodeServiceImpl.java` (Create)

* Implement CRUD, normalization, duplicate checks, and store-qualified lookup
  using only `DiscountCode` and
  `MerchantStore`. Throw the core not-found/conflict exceptions; convert
  `DataIntegrityViolationException` to the core conflict exception so races
  still reach the shop facade as 409. DTO field checks, defaults, and category
  resolution remain in `DiscountCodeFacadeImpl`.

#### 6. `sm-core/src/main/java/com/salesmanager/core/business/services/discount/DiscountCalculationService.java`, `DiscountCalculationServiceImpl.java`, and `DiscountApplicationResult.java` (Create)

* Define `PricedCartItem { ShoppingCartItem item; BigDecimal lineSubtotal; }`.
  Add `evaluate(MerchantStore store, String code,
  List<PricedCartItem> pricedItems, LocalDate today)` as the cart-level
  evaluator used by both apply and read paths. Load by
  normalized code and store, return the stored `CODE`, and evaluate the
  unavailable-product-filtered item set used by `OrderServiceImpl`. Resolve
  every category code with `CategoryService`; ignore deleted/unresolved codes.
  For each product, inspect all assigned categories and accept the item if any
  category is selected or its `/id/` lineage contains a selected ID. If
  categories are configured and none resolve, no item is eligible. Enforce
  active/date/minimum and
  eligible-item checks. Return `DiscountApplicationResult.notApplicable()`
  instead of throwing for any non-applying outcome. Calculate percent as
  `eligibleSubtotal * value / 100` at full precision, then one
  `HALF_UP` scale-2 rounding; cap amount at eligible subtotal before the same
  rounding. Never call product pricing from this service. The public
  `OrderService.preparePricedAvailableItems(ShoppingCart)` method is the only pricing
  preparation path and supplies the evaluator's `PricedCartItem` list. Run the
  evaluator in `@Transactional(readOnly = true)` scope. A product with no
  categories is eligible only when no categories are configured; it still
  counts toward the whole filtered-cart minimum in every case. The evaluator
  loads product/category rows through the store-qualified repository query
  described above. Group its rows into `Map<Long, List<ProductCategoryRow>>`
  keyed by product ID. A product ID with no entry has no categories; duplicate
  rows are harmless because eligibility is any-match. Skip this query entirely
  when the product ID collection is empty.

#### 7. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderServiceImpl.java` (Modify)

* In `caculateShoppingCart`, remove the `promoAdded` one-day branch, set
  `orderSummary.setPromoCode(cart.getPromoCode())`, and call
  `preparePricedAvailableItems(cart)`. `caculateOrder` invokes
  `DiscountCalculationService` once for the resulting item set. If the
  saved non-blank code is not applicable, `caculateOrder` returns the same
  already-built summary with no `discount` line; do not run a second
  calculation. Before returning that summary, clear only
  `ShoppingCart.promoCode` and call `shoppingCartService.saveOrUpdate(cart)`.
  If the saved code is blank, do not save the cart and add no discount line.
* In `caculateOrder`, leave every existing `OrderTotalVariation` unchanged.
  Build `List<PricedCartItem>` by calling the overload of
  `preparePricedAvailableItems` on `summary.getProducts()`; this is the single
  point where line subtotals are populated. Use those pre-variation line
  subtotals for eligibility/minimum checks. Compute
  `discount = min(computedDiscount, max(subTotal, 0))`, add one non-negative
  `OrderTotal` with exact code `discount`, and set
  `OrderTotalSummary.total = max(subTotal - discount + shipping + handling + tax, 0)` without
  changing `subTotal`. Copy the result's canonical code to
  `OrderTotalSummary.promoCode`; never put the merchant discount in the
  variation/post-processor list.

#### 8. `sm-core/src/main/java/com/salesmanager/core/business/services/order/OrderService.java` and `OrderServiceImpl.java` (Modify)

* Add public `preparePricedAvailableItems(ShoppingCart)` as the shared pricing
  path. It returns `List<PricedCartItem>` for `cart.getLineItems()` filtered to
  `product != null && product.isAvailable()`. It does not mutate items.
  `itemPrice` is the value assigned by `ShoppingCartServiceImpl`; this method
  computes `lineSubtotal` with
  `pricingService.calculatePriceQuantity(item.getItemPrice(), item.getQuantity())`.
  `caculateOrder` uses this same method on `summary.getProducts()` through an
  overload accepting the item list, and the apply path calls the same method.
  No other method computes line subtotals.
  `OrderServiceImpl.caculateShoppingCart` calls it internally, while
  `ShoppingCartFacadeImpl.modifyCart` calls it through its `OrderService`
  dependency before invoking `DiscountCalculationService.evaluate(...)`.
  `OrderServiceImpl` depends on `DiscountCalculationService`; the calculation
  service depends only on `DiscountCodeRepository` and `CategoryService`, not on
  `OrderService` or `ShoppingCartCalculationService`, so the dependency graph
  has no cycle.

#### 9. `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/PromoCodeCalculatorModule.java` (Delete) and `sm-core/src/main/java/com/salesmanager/core/business/configuration/ProcessorsConfiguration.java` (Modify)

* Remove the `PromoCodeCalculatorModule` field, import, and registration from
  `ProcessorsConfiguration.orderTotalsPostProcessors()`, then delete the class.
  The cart-level service in `OrderServiceImpl` is the sole promo calculation.
  Leave `shopizer-core-ordertotal-processors.xml`, `Constants`,
  `ManufacturerShippingCodeOrderTotalModuleImpl`, and every other
  `OrderTotalVariation` module unchanged.

#### 10. `sm-core/src/main/resources/com/salesmanager/drools/rules/PromoCoupon.drl` (Delete)

* Delete the hard-coded `Test1234` rule. No special-case code remains; a
  merchant-created `Test1234` record follows normal validation and dates.

#### 11. `sm-core-model/src/main/java/com/salesmanager/core/model/order/OrderTotalSummary.java` (Modify)

* Add nullable `promoCode` to carry the evaluator's canonical stored code from
  `OrderServiceImpl.caculateOrder` to `ReadableShoppingCartMapper`. The mapper
  uses it whenever the exact `discount` line exists, including value `0.00`.

#### 12. `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/PersistableDiscountCode.java` and `ReadableDiscountCode.java` (Create)

* Define request/response fields and JSON mapping. Keep request `type` as a
  string, use `BigDecimal` and ISO date strings, allow omitted optional fields,
  default active/start date in the service, and include `id` only in the
  response DTO. Preserve the stored merchant-written `code` exactly. Enforce
  code required/non-blank/max 100 characters; value required and >0 (PERCENT
  <=100); optional minimumSubtotal >=0; DECIMAL(19,4) persistence; null/empty
  categories as unrestricted, blank/unknown category as 400, and duplicate
  categories collapsed by the Set. PUT is full replacement, so omitted
  optional fields reset to null or create defaults.

#### 13. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/DiscountCodeFacade.java` and `DiscountCodeFacadeImpl.java` (Create)

* Map DTOs to core entities, apply defaults, validate all DTO rules and
  categories, call only `DiscountCodeService`, and translate core outcomes to
  shop `ResourceNotFoundException`, `DiscountConflictException`, and
  `DiscountValidationException`.

#### 14. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/DiscountCodeApi.java` (Create)

* Add POST/GET/PUT/DELETE mappings under `/api/v1/private/discounts`: POST
  returns 201 with `ReadableDiscountCode`; GET returns 200 with an id-ascending
  JSON array and no pagination; PUT returns 200 with the updated DTO; DELETE
  returns 200 with an empty body, matching `CategoryApi.delete`. A deleted ID
  returns 404 on later PUT/DELETE. Pass the `@ApiIgnore MerchantStore`
  resolved from `?store=` to the facade. The resolver already calls
  `userFacade.authorizeStore(store, requestURI)` for every `/private/` path;
  inside each method call
  `AuthorizationUtils.authorizeUser(authorizationUtils.authenticatedUser(),
  roles, merchantStore)` with GROUP_SUPERADMIN, GROUP_ADMIN,
  GROUP_ADMIN_CATALOGUE, and GROUP_ADMIN_RETAIL. Add controller-local
  `@ExceptionHandler` methods for
  `HttpMessageNotReadableException` and
  `MethodArgumentTypeMismatchException`; each returns `ErrorEntity` with the
  same fields as `RestErrorHandler`'s 400 handlers. Do not change global
  `RestErrorHandler` binding behavior.

#### 15. `sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/DiscountValidationException.java`, `DiscountConflictException.java`, and `RestErrorHandler.java` (Create/Modify)

* Add 400 and 409 service exceptions. Add only these two discount exception
  mappings to `RestErrorHandler`; retain its existing global handlers for other
  exceptions and use `ResourceNotFoundException` for unknown/foreign IDs.

#### 16. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java` (Modify)

* Make the promo endpoint's `modifyCart(... promo ...)` call
  `orderService.preparePricedAvailableItems(cart)`, then the shared evaluator
  before setting the code. Convert a false
  `DiscountApplicationResult.applicable` to shop
  `DiscountValidationException` (400); do not let the core evaluator throw an
  HTTP exception. Ignore promoCode values in
  `updateCartItems`, `addToCart`, `readableShoppingCart`, and the private
  `modifyCart(ShoppingCart, PersistableShoppingCartItem, ...)`; only the
  validated promo endpoint may set the cart code. Remove the one-day response
  copy in `getByCode` and let
  the mapper use the calculation result.

#### 17. `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` (Modify)

* In the `modifyCart(@PathVariable String code, @PathVariable String promo,
  ...)` handler for `POST /api/v1/cart/{code}/promo/{promo}`, rethrow
  `DiscountValidationException` unchanged alongside
  `ResourceNotFoundException`. This prevents the broad catch from wrapping the
  shopper's non-applying-code result and ensures the discount exception handler
  returns exactly HTTP 400.

#### 18. `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`, `sm-shop/src/main/java/com/salesmanager/shop/mapper/order/ReadableOrderTotalMapper.java`, and `sm-shop/src/main/java/com/salesmanager/shop/populator/order/ReadableOrderTotalPopulator.java` (Modify)

* In `merge`, make the single `shoppingCartCalculationService.calculate` call
  the only read-path calculation; `getByCode` performs none. Remove the
  `promoAdded` expiry check, set response `promoCode` only from
  `OrderTotalSummary.promoCode` when a successful `discount` line exists, and
  leave it empty otherwise. Map
  the non-negative line with exact code `discount`; preserve full `subtotal` and
  calculated `total`. Update both `ReadableOrderTotalMapper` and
  `ReadableOrderTotalPopulator` discounted-line recognition for `discount` while
  retaining compatibility with the unrelated legacy `OT_DISCOUNT_TITLE` line.
  Leave `ShoppingCartDataPopulator` unchanged because it is the legacy
  non-v1 path and obtains totals from the same calculation.

#### 19. `sm-shop/src/main/java/com/salesmanager/shop/store/controller/order/facade/OrderFacadeImpl.java` (Modify)

* In the method that builds the order total summary from the cart, remove the
  `promoAdded` expiry check and set `summary.setPromoCode(shoppingCart.getPromoCode())`
  whenever it is non-blank. `caculateOrder` re-evaluates it. If it no longer
  applies, the summary has no discount line and the order receives no discount;
  the cart is cleared and saved on its next `caculateShoppingCart` read, with
  no checkout-specific persistence.

#### 20. `sm-core/src/main/java/com/salesmanager/core/business/constants/Constants.java` and `sm-core/src/main/java/com/salesmanager/core/business/modules/order/total/ManufacturerShippingCodeOrderTotalModuleImpl.java` (Unchanged)

* Keep `OT_DISCOUNT_TITLE` and the manufacturer shipping module unchanged.
  Merchant promo totals use the literal `discount` code, and the two mapper /
  populator checks named above recognize both values.

#### 21. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/discount/DiscountCodeApiIntegrationTest.java` (Create)

* Exercise protected admin CRUD: POST returns 201 and an ID; GET lists only
  the requested store; PUT replaces fields; DELETE removes; unknown/foreign
  IDs return 404; duplicate create and case-insensitive rename return 409;
  same code is accepted in two stores. Cover 400 for blank/missing code or
  value, unknown type, percent <=0 or >100, amount <=0, end before effective
  start, unknown category, malformed JSON/date/number, and missing required
  fields. Assert an admin from store A calling with `?store=B` is rejected,
  while a superadmin may manage store B.

#### 22. `sm-shop/src/test/java/com/salesmanager/test/shop/integration/cart/ShoppingCartDiscountIntegrationTest.java` (Create)

* Create store codes and carts, then cover percent and amount discounts,
  amount cap, a `.xx5` HALF_UP case, category subtree eligibility with a
  multi-category product, whole-cart minimum subtotal (shoes 60 plus hats 50
  meets a shoes-only minimum of 100 while the discount base is 60), inclusive
  start/end dates,
  inactive codes, and another store's code. Assert every non-applying apply
  sent through `POST /api/v1/cart/{cartCode}/promo/{code}` returns exactly HTTP
  400 (including the controller catch path), and a rejected apply retains the previous code; a successful
  apply replaces it. Assert that adding or modifying an item whose JSON
  contains `promoCode` leaves the cart's existing `promoCode` unchanged.
* After application, remove items, deactivate/edit/delete the code and fetch
  the cart each time; assert the code is dropped, items remain untouched, no
  discount line remains, and a later code fix does not resurrect a persisted
  cleared code. Assert `Test1234` has no effect without an admin record.
  Verify response shape: merchant-written `promoCode`, one totals line with
  code `discount` and non-negative value (including `0.00`), full pre-discount `subtotal`, and
  `total = subtotal - discount` when no shipping, handling, or tax is present.

#### 23. `sm-core-model/src/test/java/com/salesmanager/test/discount/DiscountCodeEntityTest.java` (Create)

* Persist through the test JPA context and assert that `codeNormalized` is
  regenerated with
  `Locale.ROOT` on both `@PrePersist` and `@PreUpdate`, including a case-only
  rename.

#### 24. `sm-core/src/test/java/com/salesmanager/test/discount/DiscountCalculationServiceTest.java` (Create)

* Assert null/blank codes return `DiscountApplicationResult.notApplicable()`
  without repository lookup, and assert an applicable percentage that rounds
  to `0.00` still returns `applicable=true` with a non-negative zero discount.

#### 25. `sm-shop/src/main/java/com/salesmanager/shop/populator/cart/ShoppingCartDataPopulator.java` (Unchanged)

* This legacy non-v1 response path obtains totals from the same calculation,
  so it receives the `discount` line without a direct promo-code change.

### Verification Plan

* **Compilation/Build**: `./mvnw -DskipTests package`.
* **Unit Tests**: service tests for normalization/uniqueness, validation,
  category resolution/deletion, multi-category matching, date boundaries,
  HALF_UP arithmetic, amount cap (including a post-variation subtotal),
  the `OrderService` pricing helper, and cart-state clearing. Use a context
  startup test to ensure the order/calculation service graph has no cycle and
  persist two same-store codes differing only by case to assert the generated
  database constraint rejects the second. The integration run also exercises
  the element-collection table.
* **Integration Tests**: run
  `./mvnw -pl sm-shop -am test -Dtest='DiscountCode*Test,ShoppingCartDiscount*Test' -DfailIfNoTests=false`
  and the core discount unit tests with
  `./mvnw -pl sm-core -am test -Dtest='DiscountCalculationServiceTest,DiscountCodeEntityTest' -DfailIfNoTests=false`.
  Run the two integration classes above with the
  existing Spring test profile (`hibernate.hbm2ddl.auto=create`) against at
  least two stores; verify private authorization and store scoping.
* **Regression Checks**: existing shopping-cart and order integration tests,
  mapper tests, and any manufacturer-shipping discount tests must continue to
  pass. Confirm no code path loads `PromoCoupon.drl` and no one-day
  `promoAdded` check remains.
