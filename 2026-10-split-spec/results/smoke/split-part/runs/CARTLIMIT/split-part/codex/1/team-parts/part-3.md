Part 3 — cart enforcement and limit warnings

Own these files (and only these, plus any narrowly necessary tests):
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/**
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/**
- sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**
- sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/**
- any new cart-limit validator/exception classes in the shop modules

Enforce atomically for POST /api/v1/cart, PUT /api/v1/cart/{code}, and POST /api/v1/cart/{code}/multi; failed changes return HTTP 400 with errorCode and leave the cart (including other multi items) unchanged. Add limitWarnings to every returned cart.

Requirements from TASK.md:
- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.
- The cart, whenever it is returned, has "limitWarnings": a list of the rules it breaks now, as {"sku": "...", "rule": "MAX_PER_CART"} (with "sku": null for MAX_LINES and MAX_UNITS); an empty list when it breaks none.

Other parts provide/use:
- Part 1 provides product/store getters for limits and caps.
- Part 2 provides admin API only; do not modify its controller/DTO files.
