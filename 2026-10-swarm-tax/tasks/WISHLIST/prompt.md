Shoppers want to save products for later, and merchants want to see what shoppers are waiting for. Add a wishlist for logged-in customers, a way to move a wishlist item into a cart, and a report of the store's most wished products.

Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth/customer endpoints):

- POST /api/v1/auth/customer/wishlist with {"product": "<sku>"} adds the product and returns HTTP 201 with the wishlist. Adding a product that is already on it changes nothing and returns HTTP 200 with the wishlist.
- GET /api/v1/auth/customer/wishlist returns the wishlist.
- DELETE /api/v1/auth/customer/wishlist/{sku} removes the product and returns HTTP 204.
- POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode} moves the product into that existing cart (the cart code from the cart API): one unit is added to the cart (if the cart already holds the product, its quantity goes up by one), the product leaves the wishlist, and the response is HTTP 200 with the cart as the cart API returns it.
- The wishlist is JSON: {"count": 2, "items": [{"sku": "...", "name": "...", "price": 125.00, "available": true, "addedAt": "..."}]}, the most recently added first. "name" is the product's name, "price" its current price, "addedAt" when it was added, and "available" is true when the product is available and has stock.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {"sku": "...", "count": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.

Rules:

- Each customer sees and changes only their own wishlist.
- A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.
- A missing "product" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.
- Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.
- Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.
- When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.
