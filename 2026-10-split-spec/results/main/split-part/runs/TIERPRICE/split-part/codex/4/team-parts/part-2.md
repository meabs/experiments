Part 2 — protected admin tiers API

Add the admin REST endpoints for replacing and reading a product's quantity price tiers. Follow the same authentication/store resolution conventions used by existing /api/v1/private product APIs. The `store` query parameter selects the merchant store; product IDs must be scoped to that store.

Files owned:
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/** (new tiers controller or tier endpoint additions)
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/** (tier request/response DTOs only)

Requirements (exact task wording):
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.”
- “GET /api/v1/private/product/{id}/tiers returns the product's tiers.”
- “A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.”
- “An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.”
- “Rules:”
- “minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.”
- “A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.”
- “A rejected request changes nothing: the product keeps the tiers it had.”

Use HTTP 200 responses and JSON fields exactly as specified. Convert validation failures to 400 and cross-store/missing products to 404 without mutating stored tiers. Invoke Part 1's tier service (expected methods: getTiers(product/store), replaceTiers(product/store, list), validation/sorting) and existing ProductService store-scoped lookup.

Other parts provide:
- Part 1 provides Product tier persistence/service and atomic validation.
- Part 3 changes cart pricing independently and should not require controller changes.
