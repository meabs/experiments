# Part 2 — shopper and admin HTTP APIs

## Scope

Implement the v1 shopper alert endpoints and protected admin listing endpoints, plus request/response DTOs and mapping. Follow existing store resolution and private-endpoint security conventions. Do not edit core entities/services or `ProductInventoryFacadeImpl`; Part 1 and Part 3 own those files.

## Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` files for stock-alert shopper/admin resources.
- `sm-shop/src/main/java/com/salesmanager/shop/model/**` DTO files required only by these endpoints.
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/**` facade/mapper files required only to adapt the Part 1 service to these endpoints.

## Requirements (exact task wording)

Shopper API (no login needed, for the store given by ?store=):

- POST /api/v1/products/{sku}/alerts with {"email": "..."} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {"sku": "...", "email": "...", "status": "PENDING"}.
- DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {"id": 1, "sku": "...", "email": "...", "status": "PENDING" or "SENT", "createdAt": "...", "sentAt": null or "..."}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.
- GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {"to": "<email>", "sku": "...", "subject": "<product name> is back in stock", "createdAt": "..."}.

Rules applying to HTTP behavior:

- An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.
- A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.
- Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.

## Contract with other parts

Call the Part 1 stock-alert service for validation, idempotent create, cancellation, store-scoped listing/filtering, and outbox retrieval. Use its returned alert/outbox objects and product name to produce the exact fields/statuses above. Part 1 owns persistence and dispatch; Part 3 invokes dispatch during inventory changes.

