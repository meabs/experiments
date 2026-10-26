Part 2 — protected admin REST API and DTOs

Own these files (and only these files, unless a compile fix is strictly required for this API):

- New API/DTO classes under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/` (use the existing product/configuration API package conventions.)
- Any API-local exception/validation/support class needed under `sm-shop/src/main/java/com/salesmanager/shop/store/api/`.

Add the two protected endpoints, using the existing `/api/v1` controller conventions and injected `MerchantStore` resolved from `?store=`. Return JSON fields exactly `minPerCart`, `maxPerCart`, `packSize` and `maxLines`, `maxUnits`, including nulls. Unknown/cross-store products must map to the existing 404 mechanism. Invalid request values must map to HTTP 400 and must not persist a partial update. Ensure all endpoints are under `/private` so existing authentication protection applies.

Requirements from the task that apply to this part (exact wording):

- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “PUT /api/v1/private/product/{id}/limits with {"minPerCart": 2, "maxPerCart": 6, "packSize": 2} sets the product's limits and returns HTTP 200 with them; GET returns them. Each is optional (null when not set); setting all three to null removes the limits. An unknown product, or one from another store, gives HTTP 404 Not Found.”
- “PUT /api/v1/private/cart-rules with {"maxLines": 10, "maxUnits": 50} sets the store's caps (each optional, null for none) and returns HTTP 200 with them; GET returns them.”
- “Every limit and cap is a whole number of at least 1. minPerCart may not be more than maxPerCart, and maxPerCart may not be less than packSize. Anything else gives HTTP 400 Bad Request and keeps the old values.”

Use Part 1’s Product and MerchantStore getters/setters/services (not a second storage mechanism). The cart part relies on the DTO field names and the persisted values you expose; no cart mutation code belongs here.
