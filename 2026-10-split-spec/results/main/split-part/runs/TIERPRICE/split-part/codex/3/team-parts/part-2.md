Part 2 — private v1 tiers REST API

Scope: implement the protected /api/v1/private product tiers endpoints and their request/response DTOs, using the existing private API conventions and store query handling. Own only sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product (new or modified tiers controller/API files), sm-shop-model/src/main/java/com/salesmanager/shop/model (new tier DTOs), and focused API tests. Do not edit core persistence or cart files.

Requirements from TASK.md that apply (exact wording):

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.
- GET /api/v1/private/product/{id}/tiers returns the product's tiers.
- A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.

Rules:

- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had.

Use the existing authentication/store resolver and exception-to-status patterns so validation failures are 400 and missing/cross-store products are 404, with no partial writes.

Other parts provide: Part 1 provides the product-tier service and ordered tier records; Part 3 provides cart repricing independently. Your controller must depend only on the stable service methods and DTO fields minQuantity/price.
