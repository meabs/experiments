Part 3: inventory update correctness and restock hook.

Fix the existing inventory PUT path so products created through the product API update successfully, requests with no prices preserve existing prices, and quantity/availability transitions are detected. After saving an inventory quantity transition from zero to positive, invoke Part 1's alert dispatch exactly once; no dispatch for zero-to-zero or positive-to-positive changes. Preserve existing behavior for variants and other inventory operations.

Own these files:
- sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java
- sm-shop/src/main/java/com/salesmanager/shop/mapper/inventory/PersistableInventoryMapper.java
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java only if request binding needs correction
- closely related inventory mapper/facade tests under sm-shop/src/test/java/... if added

Part 1 provides the alert dispatch service method (accepting product/store and old/new quantities, or equivalent) and handles outbox/status updates. Part 2 consumes that service through REST and should not require changes here.
