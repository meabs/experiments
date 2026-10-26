# Part 3 — Popular report and cart integration support

## Scope

Implement the protected admin endpoint for popular wishlists and any narrowly scoped cart-facade/service adapter needed for Part 2 to add exactly one unit to an existing cart and return the normal cart representation. Keep admin authorization/store resolution consistent with existing `/api/v1/private` APIs. Do not implement customer wishlist controller routes.

## Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` new wishlist/admin report API files (or the single existing admin API file you extend)
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/**` only additions needed to expose a safe add-one/lookup operation for wishlist moves
- `sm-shop/src/main/java/com/salesmanager/shop/store/facade/**` only matching adapter methods, if required
- `sm-shop/src/main/java/com/salesmanager/shop/model/**` popular-report DTOs only

Do not edit Part 1 core wishlist persistence/service files or Part 2 customer wishlist controller/facade files.

## Requirements (exact task wording)

- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {"sku": "...", "count": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”
- “POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode} moves the product into that existing cart (the cart code from the cart API): one unit is added to the cart (if the cart already holds the product, its quantity goes up by one), the product leaves the wishlist, and the response is HTTP 200 with the cart as the cart API returns it.”
- “Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.”
- “Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.”

## Other parts provide / rely on

Part 1 provides the store-scoped `popular(store)` query and wishlist move/remove primitives. Part 2 calls the cart adapter and handles the authenticated customer identity and HTTP status mapping. Use existing admin authorization conventions and return a list of simple SKU/count objects, limited and ordered by the Part 1 query.
