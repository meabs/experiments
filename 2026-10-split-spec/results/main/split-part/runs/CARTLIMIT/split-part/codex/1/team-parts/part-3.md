Part 3 owns the cart HTTP/API error mapping and returned-cart warning representation.

Files you own (create or modify only these, plus narrowly necessary package-local tests):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java
- sm-shop/src/main/java/com/salesmanager/shop/model/shoppingcart/ReadableShoppingCart.java
- sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java
- sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**
- sm-shop/src/main/java/com/salesmanager/shop/store/api/exception/** (only a cart-limit HTTP exception/handler if needed)

Requirements (exact task wording):
- In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

Add limitWarnings to the readable DTO and populate it on every cart response (including GET and successful mutations), by inspecting current cart state and current product/store rules. Map Part 2's typed validation exception to HTTP 400 with an error body containing exactly/at least errorCode. Preserve existing 404 behavior.

Rely on Part 1's Product limit and CartRules accessors and Part 2's cart validation exception/errorCode. Do not change mutation logic outside the owned facade/API boundary.
