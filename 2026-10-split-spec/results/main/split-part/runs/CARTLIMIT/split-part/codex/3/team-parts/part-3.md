Part 3 — cart enforcement, atomicity, and warnings

Own these files (and only these files, unless a compile fix is strictly required for cart behavior):

- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacade.java` (only if a contract change is needed)
- `sm-shop/src/main/java/com/salesmanager/shop/model/shoppingcart/ReadableShoppingCart.java`
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`
- cart-specific exception/DTO classes under `sm-shop/src/main/java/com/salesmanager/shop/model/shoppingcart/` if needed.

Enforce limits before saving any cart mutation, including add, single modify, and multi modify. Validate a proposed copy first so a rejected multi request changes nothing. Throw the existing REST error mechanism with HTTP 400 and exact `errorCode` rule names. Add `limitWarnings` to every returned cart and populate current violations (including rules introduced after the cart was saved).

Requirements from the task that apply to this part (exact wording):

- “In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):”
- “A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.”
- “A cart may hold at most maxLines different products and maxUnits units in all.”
- “A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.”
- “Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.”
- “The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.”

Use Part 1’s persisted getters on Product and MerchantStore. Use Part 2’s error/DTO conventions only where necessary. Preserve existing cart pricing and unrelated behavior, and ensure successful responses include warnings for POST/PUT/multi and normal GET/read paths.
