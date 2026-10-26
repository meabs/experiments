Fix the existing inventory update path and trigger restock notifications.

Files owned:
- sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java
- sm-shop/src/main/java/com/salesmanager/shop/mapper/inventory/PersistableInventoryMapper.java (and only directly related inventory mapper files if required)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java only if request binding must be corrected for the specified endpoint
- Focused inventory tests under sm-shop/src/test/** if added

Requirements (exact task wording):
- Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {"productId": ..., "quantity": ..., "available": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.
- When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.

Capture the old quantity before merge/save, resolve the owning Product robustly for products created through the product API, make prices optional while preserving existing prices when omitted, save successfully, then call Part 1's StockAlertService.notifyRestocked only for a zero-to-positive transition. Do not send for unrelated products or non-transition updates.

Other parts provide:
- Part 1 provides StockAlertService.notifyRestocked(Product, MerchantStore, oldQuantity, newQuantity) (or an equivalent clearly named method) and the persistence behavior.
- Part 2 exposes the API resources and consumes the resulting alert/outbox records.
