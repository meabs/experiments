Part 2 owns the logged-in customer wishlist REST API. Read TASK.md first.

Implement POST/GET/DELETE /api/v1/auth/customer/wishlist and POST /api/v1/auth/customer/wishlist/{sku}/cart/{cartCode}, including authentication/authorization consistent with existing auth/customer endpoints, request validation, exact HTTP statuses and exception mapping. Use the wishlist service from Part 1 and the existing ShoppingCartFacade (notably addToCart(Customer, PersistableShoppingCartItem, MerchantStore, Language) and cart lookup/modify methods) to move one unit, then remove the wishlist entry only after a successful cart update.

Files owned (create or modify only these):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/WishlistApi.java (or an equivalently named customer API controller)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/** only if a narrowly required wishlist-specific exception mapping is needed
- sm-shop-model/src/main/java/com/salesmanager/shop/model/** only for request DTOs if Part 1 does not supply them

Rely on Part 1's wishlist service/DTO methods and existing MerchantStore, Language, CustomerFacade/security and cart facade APIs. Do not edit persistence/service implementation or admin controllers.
