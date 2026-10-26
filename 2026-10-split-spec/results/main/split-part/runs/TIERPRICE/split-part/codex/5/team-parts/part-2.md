# Part 2 — protected admin tiers API and JSON DTO

## Scope

Add the v1 private product tiers endpoints and request/response representation. Do not edit core model/service or cart files; consume Part 1's `productTierService` contract.

## Files owned

- `sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/ProductTier.java` (or an equivalently named DTO file in this package)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductTierApi.java` (new)
- Any API-local exception/validation helper under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/` needed only by this endpoint

## Requirements (exact task wording)

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.
- GET /api/v1/private/product/{id}/tiers returns the product's tiers.
- A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.

Rules:

- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had.

## Integration contract

Inject Part 1's `ProductTierService` bean named `productTierService`; use its store-aware product lookup and atomic replacement methods. Convert DTOs to core `ProductTier` objects and back. Use the same `MerchantStore` resolution and authentication annotations/conventions as existing `/api/v1/private/product/...` controllers. Return explicit 200/404/400 statuses (including malformed/non-integral `minQuantity`, null fields, duplicate quantities, >10 tiers, and ordering/price violations).

## Checks

Run the relevant `sm-shop` compile/tests and, if practical, endpoint tests. Do not change unrelated APIs.
