# Part 2 — Authenticated customer wishlist REST API

## Scope

Implement the customer-facing wishlist request/response DTOs, facade methods, and REST controller endpoints under `sm-shop`. Follow the existing authenticated customer pattern (`HttpServletRequest#getUserPrincipal`, `/api/v1/auth/customer/...`, merchant store and language argument resolvers). Implement add, list, delete, and move-to-cart orchestration by calling Part 1’s wishlist service and the existing cart facade.

## Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/**` wishlist API/controller files you add (do not alter unrelated customer APIs)
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/customer/facade/**` only wishlist facade interface/implementation additions
- `sm-shop/src/main/java/com/salesmanager/shop/model/**` wishlist request/response DTOs and mappers/populators needed by these endpoints

Do not edit core repositories/services owned by Part 1 or admin/report files owned by Part 3.

## Requirements (exact task wording)

- “Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth/customer endpoints):”
- “POST /api/v1/auth/customer/wishlist with {"product": "<sku>"} adds the product and returns HTTP 201 with the wishlist. Adding a product that is already on it changes nothing and returns HTTP 200 with the wishlist.”
- “GET /api/v1/auth/customer/wishlist returns the wishlist.”
- “DELETE /api/v1/auth/customer/wishlist/{sku} removes the product and returns HTTP 204.”
- “POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode} moves the product into that existing cart (the cart code from the cart API): one unit is added to the cart (if the cart already holds the product, its quantity goes up by one), the product leaves the wishlist, and the response is HTTP 200 with the cart as the cart API returns it.”
- “The wishlist is JSON: {"count": 2, "items": [{"sku": "...", "name": "...", "price": 125.00, "available": true, "addedAt": "..."]}, the most recently added first. "name" is the product's name, "price" its current price, "addedAt" when it was added, and "available" is true when the product is available and has stock.”
- “Each customer sees and changes only their own wishlist.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.”
- “A missing "product" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.”
- “Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.”
- “Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.”

## Other parts provide / rely on

Part 1 provides wishlist service methods and domain exceptions/results. Existing `ShoppingCartFacade`/v1 cart facade provides add-one-to-existing-cart and cart lookup/population; use its established `ReadableShoppingCart` response shape. Part 3 owns the admin popular endpoint and must not be required by these routes.
