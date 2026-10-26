# Part 1 — Wishlist persistence and domain service

## Scope

Implement the wishlist data model, repositories, and core service in `sm-core` (plus any matching model classes in `sm-shop-model` if needed). Integrate product deletion cleanup here. Do not implement REST controllers; expose clear service methods for the API parts.

## Files owned

- `sm-core/src/main/java/com/salesmanager/core/model/**` wishlist-related model files you add
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/**` wishlist repository files you add or modify
- `sm-core/src/main/java/com/salesmanager/core/business/services/**` wishlist service files you add or modify
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**` only the product-deletion hook needed to remove wishlist entries
- corresponding `sm-shop-model/src/main/java/com/salesmanager/shop/model/**` DTOs only if the service/API contract requires them

Avoid editing REST API/controller files owned by Parts 2–3.

## Requirements (exact task wording)

- “Shoppers want to save products for later, and merchants want to see what shoppers are waiting for. Add a wishlist for logged-in customers, a way to move a wishlist item into a cart, and a report of the store's most wished products.”
- “The wishlist is JSON: {"count": 2, "items": [{"sku": "...", "name": "...", "price": 125.00, "available": true, "addedAt": "..."]}, the most recently added first. "name" is the product's name, "price" its current price, "addedAt" when it was added, and "available" is true when the product is available and has stock.”
- “Each customer sees and changes only their own wishlist.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.”
- “A missing "product" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.”
- “Removing or moving a product that is not on the customer's wishlist, or moving to a cart that does not exist, gives HTTP 404 Not Found.”
- “Moving a product that is not available or has no stock gives HTTP 409 Conflict; the cart and the wishlist do not change.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”

## Other parts provide / rely on

Expose methods with obvious equivalents to `getWishlist(customer, store, language)`, `add(customer, sku, store, language)`, `remove(customer, sku, store)`, `contains/getEntry`, and `popular(store)`. Part 2 will call the add/get/remove operations and needs domain exceptions that can map to 400/404/409. Part 3 will call the popular query and the move operation or the low-level removal after a successful cart add. Keep customer/store scoping explicit and preserve newest-first ordering and a 50-item limit.
