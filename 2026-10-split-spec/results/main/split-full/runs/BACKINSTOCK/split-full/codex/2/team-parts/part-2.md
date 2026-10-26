Part 2: REST APIs.

Add shopper endpoints POST /api/v1/products/{sku}/alerts and DELETE /api/v1/products/{sku}/alerts, plus protected admin GET /api/v1/private/stock-alerts and GET /api/v1/private/stock-alerts/outbox. Match existing controller conventions/security/store resolution. Implement exact HTTP statuses and validation/error behavior from TASK.md, including status filtering and response JSON fields/order. Do not implement persistence or inventory transition logic here; inject and use Part 1's alert service contract.

Own these files/directories:
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/... stock-alert controller(s) and request/response classes if API-local
- sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/... only if a narrowly scoped exception handler is required for these endpoints
- sm-shop/src/test/java/... stock-alert API tests may be added

Part 1 provides the alert service, entities/DTOs, and methods for create/cancel/list/outbox. Part 3 updates inventory and invokes Part 1 dispatch; this part only exposes the HTTP surface.
