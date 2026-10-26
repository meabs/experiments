## Part 3: inventory update compatibility and restock integration

Fix the existing private inventory PUT flow so products created through the product API can be updated, updates with no prices preserve existing prices, and the documented payload works. Ensure the flow correctly identifies the product/inventory, handles null/empty prices, and preserves current behavior for variants. After a successful save, invoke Part 1's stock-alert restock hook so zero-to-positive transitions send alerts, while all other transitions do nothing.

Own `sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java`, inventory mappers/models/controllers directly implementing the PUT inventory endpoint, and any narrowly-scoped tests or support files needed for this compatibility fix. Avoid editing the new alert API/controllers or core alert domain files.

Part 1 provides a public restock callback on its alert service. Part 2 consumes the resulting alert/outbox data but should not require changes from this part.
