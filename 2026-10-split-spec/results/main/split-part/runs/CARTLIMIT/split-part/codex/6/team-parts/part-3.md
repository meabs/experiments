Part 3 — cart enforcement and limit warnings

Scope and owned files

- Own cart mutation and representation files, principally `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`, cart-related facade/helpers, and `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java`.
- Own cart response model files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/` needed to expose warnings, plus focused cart exception/error handling if required.
- Do not edit Product/MerchantStore domain fields or admin API controller/DTO files owned by Parts 1 and 2.

Requirements from TASK.md that apply to this part (exact wording)

- “In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):”
- “A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.”
- “A cart may hold at most maxLines different products and maxUnits units in all.”
- “A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.”
- “Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.”
- “The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.”

Implementation contract for other parts

- Consume Part 1’s Product nullable limit getters and MerchantStore nullable cap getters directly.
- Keep all mutation validation transactional/atomic: validate the complete prospective cart before deleting, adding, or changing any persisted line; multi-request failures must not partially apply.
- Ensure the API layer can serialize a 400 with an `errorCode` string exactly matching the rule constants above (define/reuse a focused exception contract without changing unrelated endpoints).
- Add `limitWarnings` to the readable cart JSON with warning objects containing `sku` and `rule`; compute warnings on every returned cart, including carts that became invalid after an admin rule change.
