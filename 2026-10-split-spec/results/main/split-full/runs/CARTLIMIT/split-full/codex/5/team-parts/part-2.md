Part 2 owns the protected admin REST API and DTOs for configuring limits.

Files owned: sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductApi.java (or a new limits controller in the same package); new DTOs under sm-shop/src/main/java/com/salesmanager/shop/model; and any API exception/validation handler additions needed solely for these endpoints.

Implement PUT/GET /api/v1/private/product/{id}/limits and PUT/GET /api/v1/private/cart-rules, using the existing MerchantStore argument/security conventions and ?store scoping. Return 200 payloads, 404 for missing/cross-store products, and 400 while preserving old values for invalid requests. Consume Part 1's product/store limits service and validator; expected methods are getProductLimits/updateProductLimits and getCartRules/updateCartRules (adapt names if implementation differs). Do not change cart facades or persistence entities directly.
