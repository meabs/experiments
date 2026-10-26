Part 3 — cart enforcement and warnings

Implement enforcement and response warnings for all requested cart mutation endpoints. Own only cart API/facade/service/populator/mapper/model response files and cart-specific exception handling. Do not edit admin controllers or limits persistence/service files owned by Parts 1 and 2.

Requirements from TASK.md that apply:

In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):

- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

Ensure validation is atomic for multi changes and occurs before persistence. Preserve existing endpoint status conventions except rejected changes must be HTTP 400 with the named errorCode. Add limitWarnings to every returned cart representation, including GET and successful mutations.

Files owned: sm-shop cart API/facade/service/populator/mapper and sm-shop-model cart response/request classes, plus cart-specific tests. Do not modify Part 1's settings model/service or Part 2's admin controller files.

Other parts rely on: Part 1's ProductLimits, CartRules, and service lookup methods. Use product SKU for product-rule warnings and null SKU for aggregate MAX_LINES/MAX_UNITS warnings.
