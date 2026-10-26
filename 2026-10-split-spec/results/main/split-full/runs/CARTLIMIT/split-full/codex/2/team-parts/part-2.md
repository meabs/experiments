Read TASK.md first. Own the protected admin HTTP API and its request/response DTOs for product limits and store cart rules. Implement PUT/GET /api/v1/private/product/{id}/limits and /api/v1/private/cart-rules, including store query scoping, 404 for missing/wrong-store products, 400 validation while retaining old values, and 200 responses. Follow existing private API authentication/controller conventions and error payload conventions.

Files owned: new or directly related files under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/** for these endpoints and DTOs under sm-shop-model/src/main/java/com/salesmanager/shop/model/**. Avoid editing cart API/facade files or core domain files owned by part 1.

Rely on part 1's Product/MerchantStore limit fields and service accessors. Keep JSON property names exactly minPerCart, maxPerCart, packSize, maxLines, maxUnits; null means unset/removal.
