Part 2 — authenticated customer wishlist API and move-to-cart

Own sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/WishlistApi.java (or equivalent customer API file), wishlist-facing DTO/request classes under sm-shop/src/main/java/com/salesmanager/shop/model/, and the shopping-cart integration files needed to add one unit to an existing cart. Do not edit core wishlist persistence files or admin API files.

Requirements (exact task wording):
- "Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth/customer endpoints):"
- "POST /api/v1/auth/customer/wishlist with {\"product\": \"<sku>\"} adds the product and returns HTTP 201 with the wishlist. Adding a product that is already on it changes nothing and returns HTTP 200 with the wishlist."
- "GET /api/v1/auth/customer/wishlist returns the wishlist."
- "DELETE /api/v1/auth/customer/wishlist/{sku} removes the product and returns HTTP 204."
- "POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode} moves the product into that existing cart (the cart code from the cart API): one unit is added to the cart (if the cart already holds the product, its quantity goes up by one), the product leaves the wishlist, and the response is HTTP 200 with the cart as the cart API returns it."
- "Each customer sees and changes only their own wishlist."
- "A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request."
- "A missing \"product\" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found."
- "Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found."
- "Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change."

Rely on Part 1's wishlist service and its exception/status distinctions. Rely on existing customer authentication via HttpServletRequest Principal, MerchantStore/Language injection, and existing ShoppingCartFacade methods; add a one-unit operation if necessary and return existing ReadableShoppingCart JSON. Ensure atomic behavior for failed moves.
