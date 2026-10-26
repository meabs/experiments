# Part 3 — inventory update integration and price-preserving fix

## Scope

Fix the existing private inventory PUT path so product-API-created products and requests without prices work, preserve existing prices when prices are omitted, and trigger Part 1 restock dispatch only on a zero-to-positive quantity transition. Do not edit stock-alert entities/services or HTTP alert resources.

## Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java`.
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/inventory/**` files needed for merge/conversion price behavior.
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java` only if required to correct request field handling.
- Closely related inventory facade/model tests under `sm-shop/src/test/**` if adding tests.

## Requirements (exact task wording)

- When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.
- Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {"productId": ..., "quantity": ..., "available": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.
- After a product sells out again, the same email can ask again, which makes a new pending alert.

## Contract with other parts

Before saving, obtain the actual existing `ProductAvailability` and its product safely even for products created through the product API; merge quantity/available and leave its prices untouched when the request has no prices. After a successful save, call Part 1's stock-alert service method (for example `onStockUpdated(product, store, oldQuantity, newQuantity)`) so it can dispatch only a zero-to-positive transition. Do not dispatch for unrelated updates.

