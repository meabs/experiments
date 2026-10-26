Part 2 — authenticated customer wishlist API and cart move

Own only these files/directories (create new files under them as needed):
- sm-shop-model/src/main/java/com/salesmanager/shop/model/wishlist/
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/ (wishlist controller/API files only)
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/wishlist/ (if a facade/mapper is useful)

Implement the logged-in customer endpoints, authentication/ownership checks, request/response DTOs and HTTP statuses. Use request.getUserPrincipal() and the existing customer facade patterns. For moving to a cart, verify wishlist membership and cart existence, reject unavailable/no-stock with 409 without changing either resource, add exactly one unit through the existing cart facade, then remove the wishlist entry and return the cart representation.

Requirements from TASK.md that apply to this part (exact words):
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

Part 1 provides the wishlist service/model methods. Existing ShoppingCartFacade.modifyCart/addToCart and getByCode/readable cart methods provide cart behavior; do not edit files owned by other parts.
