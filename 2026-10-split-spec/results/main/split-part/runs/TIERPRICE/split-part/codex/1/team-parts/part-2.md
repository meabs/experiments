Part 2 — private tiers API and transport models

Implement the admin HTTP API and its shop-facing DTO/facade. Own only these files (new files are allowed under these directories):

- `sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/tier/` (all new request/response DTOs)
- `sm-shop-model/src/main/java/com/salesmanager/shop/store/controller/product/facade/` new tier facade interface(s)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/` new tier API controller file(s)
- `sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/` new tier facade implementation file(s), if that is the project’s implementation package

Requirements from TASK.md that apply to this part (exact wording):

"Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.
- GET /api/v1/private/product/{id}/tiers returns the product's tiers.
- A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- An unknown product, or one that belongs to another store, gives HTTP 404 Not Found."

"Rules:

- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had."

Use the same `@ApiIgnore MerchantStore merchantStore` binding and controller conventions as existing `/api/v1/private` product APIs. Return concrete 200/400/404 statuses and ensure malformed/missing fields cannot partially persist. Depend on Part 1’s tier service methods (expected names `getTiers(...)` and `replaceTiers(...)`) and Product store lookup; do not edit Part 1 files.

Run focused API/module tests or compilation if practical.
