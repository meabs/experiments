Part 2 — shopper/admin stock-alert HTTP API and shop DTOs

Own these files (and only these areas):
- sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/stockalert/** (request/response DTOs)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/StockAlertApi.java (new controller; adjust only directly related exception mapping if required)

Build the unauthenticated shopper endpoints and protected admin endpoints, resolving the store from the existing @ApiIgnore MerchantStore mechanism and following conventions of neighboring v1 APIs. Validate email (missing/invalid -> 400), map unknown SKU to 404, in-stock subscribe to 409, duplicate pending subscribe to 200, new subscribe to 201, successful cancel to 204, missing/already-sent cancel to 404. Admin status filtering accepts only PENDING or SENT; any other value is 400. Serialize exactly the requested fields and ordering (oldest first), including null sentAt for pending.

Exact task requirements applying to this part:
- “POST /api/v1/products/{sku}/alerts with {"email": "..."} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {"sku": "...", "email": "...", "status": "PENDING"}. ”
- “DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.”
- “GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {"id": 1, "sku": "...", "email": "...", "status": "PENDING" or "SENT", "createdAt": "...", "sentAt": null or "..."}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.”
- “GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {"to": "<email>", "sku": "...", "subject": "<product name> is back in stock", "createdAt": "..."}.”
- “An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”
- “A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.”

Part 1 provides the stock-alert service and entities; call those methods rather than accessing repositories directly. Part 3 provides inventory transition notifications through the service.
