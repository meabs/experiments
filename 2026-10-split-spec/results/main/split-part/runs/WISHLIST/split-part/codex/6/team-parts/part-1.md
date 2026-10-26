Part 1 — wishlist domain and business service

Implement the persistent wishlist domain and service layer, including all validation, product deletion cleanup, popular aggregation, and the operation that adds a wishlist product to an existing cart. Own only new/changed files under sm-shop-model/src/main/java/com/salesmanager/shop/model (wishlist DTO/entity packages), sm-core/src/main/java/com/salesmanager/core/business/repositories (wishlist repositories), sm-core/src/main/java/com/salesmanager/core/business/services (wishlist service), and the existing product/cart service files needed for deletion cleanup or cart insertion. Do not edit API controller files.

Requirements applying to this part (exact task wording):

- The wishlist is JSON: {"count": 2, "items": [{"sku": "...", "name": "...", "price": 125.00, "available": true, "addedAt": "..."}]}, the most recently added first. "name" is the product's name, "price" its current price, "addedAt" when it was added, and "available" is true when the product is available and has stock.
- Each customer sees and changes only their own wishlist.
- A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.
- A missing "product" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.
- Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.
- Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.
- When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.
- GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {"sku": "...", "count": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.

Provide stable public service methods for the API parts to call (names/signatures should make intent clear), e.g. list(customer, store), add(customer, sku, store), remove(customer, sku, store), moveToCart(customer, sku, cartCode, store, language), and popular(store). Preserve transactionality for move failure and deletion cleanup.

Part 2 supplies the customer controller and DTO/request binding; Part 3 supplies the private admin controller. They depend on these service methods and returned model/readable types.
