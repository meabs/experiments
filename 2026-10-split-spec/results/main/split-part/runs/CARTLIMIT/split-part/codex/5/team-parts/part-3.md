# Part 3 — Cart enforcement, atomic multi-updates, and warnings

## Ownership

Own only cart-facing shop files: `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java`, its `ShoppingCartFacade` interface if needed, `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`, cart mapper/populator files such as `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/ReadableShoppingCartMapper.java` and `sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartDataPopulator.java`, and cart response models under `sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/`. Avoid files owned by Parts 1–2.

## Requirements (exact task wording)

In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):

- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

## Implementation guidance/contracts

Validate a candidate snapshot before mutating/persisting the cart, and for multi requests stage every requested change then commit only if all pass. Quantity 0 always removes a line without product-line validation. Product limits are checked on lines added/changed; maxLines/maxUnits are only checked when the attempted operation increases line count/units, allowing corrective edits to an already-invalid cart. Raise the existing shop REST exception type in a way that yields HTTP 400 and exact `errorCode` values above.

Add a serializable response property `limitWarnings` to `ReadableShoppingCart`, with entries containing `sku` (nullable) and `rule`; ensure every cart response path (POST, PUT, multi, GET and returned delete/body paths if applicable) populates it from the current cart and current Product/MerchantStore rules. Warnings must report all currently broken rules, including store caps with null SKU, and be an empty list when none. Use Part 1's nullable model getters directly (`Product.getMinPerCart`, `getMaxPerCart`, `getPackSize`, `MerchantStore.getMaxLines`, `getMaxUnits`).

Preserve existing successful status codes/shapes unless the task explicitly changes them. Run focused Maven compilation/tests for the modules you touch.
