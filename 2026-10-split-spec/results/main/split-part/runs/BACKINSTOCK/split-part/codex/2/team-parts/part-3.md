# Part 3: inventory update correctness and restock hook

## Scope and owned files

Own inventory update path files, chiefly `sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java`, `sm-shop/src/main/java/com/salesmanager/shop/mapper/inventory/PersistableInventoryMapper.java`, and directly related inventory API/model files if needed. Do not modify Part 1 core alert files or Part 2 alert controllers/DTOs.

## Requirements (exact task wording)

“When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”

“Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {\"productId\": ..., \"quantity\": ..., \"available\": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.”

“A product with alerts can still be deleted as before, and its alerts go with it.”

## Contract for other parts

Inject the Part 1 alert service transition method (for example `onInventoryQuantityChanged(Product product, int oldQuantity, int newQuantity)`) after a successful availability save, passing the pre-update quantity and new quantity. Preserve existing prices when `PersistableInventory.prices` is null/omitted; avoid null dereferences and ensure products created through the product API resolve their availability/product correctly. Part 2 exposes the inventory endpoints unchanged and will read the outbox/alert states produced here.
