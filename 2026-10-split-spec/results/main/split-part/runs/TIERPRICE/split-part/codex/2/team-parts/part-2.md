Part 2 — private admin tiers API and JSON contract

Add the protected product tiers endpoints in the existing v1 private API style, using the request’s ?store= resolved MerchantStore. Add the JSON request/response type and HTTP validation/error handling. Unknown products and products belonging to another store must be 404. PUT must be atomic via Part 1’s service and return the stored ordered list.

Files owned (and only these unless a directly required adjacent test is needed):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/** (API controller additions; avoid changing unrelated endpoints)
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/** (tier request/response DTOs)

Exact task requirements applying to this part:
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.”
- “GET /api/v1/private/product/{id}/tiers returns the product's tiers.”
- “A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.”
- “An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.”
- “minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.”
- “A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.”
- “A rejected request changes nothing: the product keeps the tiers it had.”

Other parts provide/rely on:
- Part 1 provides the tier entity/value type and service methods (for example getTiers and replaceTiers) and store-scoped product lookup/validation.
- Part 3 independently consumes the persisted product tiers when recalculating carts; do not put cart pricing logic in this part.
