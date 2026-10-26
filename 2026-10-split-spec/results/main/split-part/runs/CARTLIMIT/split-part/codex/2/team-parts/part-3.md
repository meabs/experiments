Part 3 — cart enforcement and limit warnings

Own these files (and only these areas):
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java` and its interface if required.
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java` only for mapping validation failures to HTTP 400/errorCode.
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java` and/or cart populators.
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/ReadableShoppingCart.java` and new warning/error DTOs.

Requirements (exact task wording):
- In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):
- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

Use Part 1's product-limit/store-rule services. Validate a prospective copy before persistence so multi requests are atomic, allow quantity 0 removal, apply caps only on additions/increased units as specified, and calculate warnings on every returned cart (including carts made invalid by later rule changes). Preserve existing response behavior/statuses except rejected mutations must be HTTP 400 with `errorCode`.
