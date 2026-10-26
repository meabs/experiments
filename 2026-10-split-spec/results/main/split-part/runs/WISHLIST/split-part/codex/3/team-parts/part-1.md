# Part 1: wishlist domain and core service

Implement the persistent wishlist domain and service layer. Own only files under `sm-core-model/src/main/java/com/salesmanager/core/model/wishlist/**`, `sm-core/src/main/java/com/salesmanager/core/business/repositories/wishlist/**`, and `sm-core/src/main/java/com/salesmanager/core/business/services/wishlist/**`; you may also add the smallest necessary product-delete event listener/configuration file under `sm-core/src/main/java/com/salesmanager/core/business/configuration/events/products/listeners/**` to remove deleted products from wishlists. Do not edit API files owned by parts 2 or 3.

Requirements from TASK.md that apply:

- “The wishlist is JSON: {\"count\": 2, \"items\": [{\"sku\": \"...\", \"name\": \"...\", \"price\": 125.00, \"available\": true, \"addedAt\": \"...\"}]}, the most recently added first. \"name\" is the product's name, \"price\" its current price, \"addedAt\" when it was added, and \"available\" is true when the product is available and has stock.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.” (Expose a domain/service error that the customer API can map to 400.)
- “A missing \"product\" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.”
- “Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.”
- “Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”
- For the admin aggregation: “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”

Provide a `WishlistService` (and implementation/repository) with clear methods for listing a customer's store-scoped wishlist, add/remove, moving/consuming an item in an existing cart, and obtaining popular SKU/count rows. It must enforce customer isolation, 50-item limit, newest-first ordering, and atomic move semantics. Use existing `ProductService`, inventory/availability, and `ShoppingCartService` APIs as appropriate. Expose DTO/projection classes or plain records needed by the API parts, including item fields and popular `{sku,count}`.

Other parts rely on these symbols: part 2 will inject `WishlistService` and call customer-scoped list/add/remove/move methods; part 3 will inject `WishlistService` and call a store-scoped `popular(...)` method returning SKU/count rows. Keep method names/signatures discoverable and document any checked exceptions so API code can map statuses.
