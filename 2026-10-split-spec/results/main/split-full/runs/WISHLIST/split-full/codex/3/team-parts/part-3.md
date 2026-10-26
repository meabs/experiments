Part 3 owns the protected merchant popular-wishlist report endpoint and cart integration needed by the customer move operation. Read TASK.md first.

Implement GET /api/v1/private/wishlists/popular with store scoping, existing private-admin authentication/authorization conventions, ordering (count descending, SKU ascending), and max 10 response entries, delegating aggregation to Part 1's wishlist service. Also extend the existing shopping-cart facade/API only as needed to reliably find an existing cart by code, add exactly one SKU for a customer, preserve existing cart response shape/status behavior, and ensure a failed move (missing cart/unavailable/no stock) leaves both cart and wishlist unchanged.

Files owned (create or modify only these):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/** admin wishlist report controller files
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacade.java
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java
- sm-shop-model/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/v1/ShoppingCartFacade.java if its contract must be extended

Rely on Part 1's WishlistService.popular(...) and existing ProductService/availability services. Part 2 will invoke your cart facade methods. Do not edit the wishlist persistence layer or customer API controller.
