Part 3 — inventory update correctness and restock trigger

Own these files (and only these areas):
- sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java
- sm-shop/src/main/java/com/salesmanager/shop/mapper/inventory/PersistableInventoryMapper.java
- sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/inventory/PersistableInventory.java and related inventory DTO files only if required
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java only if required for the specified PUT behavior

Fix the existing PUT inventory path so products created through the product API update successfully, and an update request with no prices preserves existing prices. Detect the old and new quantity/stock state and invoke the stock-alert service only on a zero-to-positive transition; do not notify for zero-to-zero or positive-to-positive. Preserve existing behavior for variants and store checks.

Exact task requirements applying to this part:
- “Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {"productId": ..., "quantity": ..., "available": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once...”
- “Changing stock that stays at zero, or raising stock that is already above zero, sends nothing...”

Part 1 provides a notifyRestocked(Product, MerchantStore) (or equivalent) service method. Call it after the availability is persisted and only for a genuine zero-to-positive transition. Do not implement HTTP alert endpoints (Part 2 owns those).
