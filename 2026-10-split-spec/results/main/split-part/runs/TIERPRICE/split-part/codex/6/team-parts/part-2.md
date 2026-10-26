Part 2 — protected v1 admin tiers API

Implement the REST endpoint and request/response DTOs. Own only files under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/** and sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/** (create focused tier DTO files there). Do not edit core model/service or cart files.

Requirements (exact task wording):
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

  - PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.
  - GET /api/v1/private/product/{id}/tiers returns the product's tiers.
  - A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
  - An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.”
- “Rules:

  - minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
  - A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
  - A rejected request changes nothing: the product keeps the tiers it had.”

Match existing v1 controller conventions/security/store injection and exception handling so private endpoints are protected. Use ProductTierService methods supplied by Part 1; map service validation failures to 400 and missing/wrong-store products to 404. Return exactly the tier JSON fields and sorted order.
