# Part 3 — inventory update compatibility and restock hook

Fix the existing inventory update path and connect successful stock transitions to alert sending. Own `sm-shop/src/main/java/com/salesmanager/shop/store/facade/product/ProductInventoryFacadeImpl.java`, `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductInventoryApi.java`, and directly related inventory mapper/model files only when necessary. Do not edit stock-alert persistence or alert REST controllers owned by Parts 1–2.

Requirements (exact task wording):

- “Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {\"productId\": ..., \"quantity\": ..., \"available\": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”

Ensure product/availability lookup cannot dereference a missing origin set for products created through the product API; merge quantity/available while retaining existing prices when request prices are absent. Capture old quantity and invoke Part 1’s stock-transition service only after the inventory save succeeds, with store/product context. Keep existing API contract and security.

Other parts provide: Part 1 supplies the stock-alert transition method (coordinate exact class/method names); Part 2 exposes the endpoints and relies on this inventory path.
