Implement the shopper and admin HTTP APIs plus shop-layer DTO/facade adapter.

Files owned:
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/stockalert/** (request/response DTOs)
- sm-shop-model/src/main/java/com/salesmanager/shop/store/controller/product/facade/StockAlertFacade.java (new interface)
- sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/StockAlertFacadeImpl.java (adapter/validation/mapping)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/StockAlertApi.java (or equivalent API controller files for these endpoints)
- Any shop-layer tests directly covering these endpoints, if added

Requirements (exact task wording):
Shopper API (no login needed, for the store given by ?store=):

- POST /api/v1/products/{sku}/alerts with {"email": "..."} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {"sku": "...", "email": "...", "status": "PENDING"}.
- DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {"id": 1, "sku": "...", "email": "...", "status": "PENDING" or "SENT", "createdAt": "...", "sentAt": null or "..."}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.
- GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {"to": "<email>", "sku": "...", "subject": "<product name> is back in stock", "createdAt": "..."}.

Rules at the HTTP boundary (map service/domain failures to these statuses):
- An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.
- A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.
- Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.

Use the existing MerchantStore/Language injection and private endpoint security conventions. Preserve exact JSON field names and status codes. The facade should rely on Part 1's StockAlertService methods/entities and not duplicate persistence.

Other parts provide:
- Part 1 provides StockAlertService and alert/outbox entities with create/cancel/list/listOutbox operations.
- Part 3 invokes Part 1 when inventory changes; this API only reads the resulting state.
