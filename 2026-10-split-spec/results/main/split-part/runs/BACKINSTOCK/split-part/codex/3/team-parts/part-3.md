Part 3 – inventory update and stock transition integration

Own these files: sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java; sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java; inventory mappers/models in sm-shop if required; and only closely related inventory/core availability files needed to make this update reliable. Do not edit alert API files owned by Part 2 or alert domain/repository files owned by Part 1.

Fix inventory PUT behavior for products created through the product API and for payloads with no prices. Preserve existing prices when prices are omitted. Capture old quantity before saving and notify the Part 1 alert service only for a transition from zero to more than zero; do not notify for zero->zero or positive->positive. Keep existing inventory endpoint paths and store/security behavior.

Requirements from TASK.md applying here:

- “Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {\"productId\": ..., \"quantity\": ..., \"available\": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”

Part 1 provides the stock-transition processing method/service; invoke it after a successful update with the product/store and old/new quantities. Part 2 depends on the resulting persisted alert/outbox state.
