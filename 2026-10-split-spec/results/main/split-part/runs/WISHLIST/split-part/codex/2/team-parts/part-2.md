# Part 2 — customer wishlist endpoints and cart move

Implement the authenticated customer HTTP API and its DTOs/facade integration. Own files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/**` (wishlist endpoint files only), `sm-shop/src/main/java/com/salesmanager/shop/model/wishlist/**`, and customer/cart facade files needed solely for these endpoints. Do not edit the core wishlist model/service files owned by Part 1 or the admin endpoint owned by Part 3.

Requirements (exact task wording):

- “Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth/customer endpoints):”
- “POST /api/v1/auth/customer/wishlist with {\"product\": \"<sku>\"} adds the product and returns HTTP 201 with the wishlist. Adding a product that is already on it changes nothing and returns HTTP 200 with the wishlist.”
- “GET /api/v1/auth/customer/wishlist returns the wishlist.”
- “DELETE /api/v1/auth/customer/wishlist/{sku} removes the product and returns HTTP 204.”
- “POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode} moves the product into that existing cart (the cart code from the cart API): one unit is added to the cart (if the cart already holds the product, its quantity goes up by one), the product leaves the wishlist, and the response is HTTP 200 with the cart as the cart API returns it.”
- “The wishlist is JSON: {\"count\": 2, \"items\": [{\"sku\": \"...\", \"name\": \"...\", \"price\": 125.00, \"available\": true, \"addedAt\": \"...\"}]}, the most recently added first. \"name\" is the product's name, \"price\" its current price, \"addedAt\" when it was added, and \"available\" is true when the product is available and has stock.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.”
- “A missing \"product\" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.”
- “Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.”
- “Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.”

Use the same principal/token authentication and exception-to-status conventions as existing `/api/v1/auth/customer` endpoints. Ensure duplicate add is 200, first add 201, and move is atomic with respect to availability/conflict. Return the established cart representation (`ReadableShoppingCart`) exactly as the cart API does.

Other parts provide: Part 1 provides the wishlist service/domain methods and popular aggregation; existing shopping-cart services/facades provide cart lookup, add-one/increment, and cart population. Part 3 independently consumes Part 1’s popular method.
