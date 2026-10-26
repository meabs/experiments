Part 2 owns cart mutation enforcement in the shopping-cart facade/service. Make all single and multi changes atomic and validate against the services supplied by Part 1.

Files you own (create or modify only these, plus narrowly necessary package-local tests):
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacadeImpl.java
- sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/ShoppingCartFacade.java
- sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/** (only enforcement helpers/integration)
- sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/** (only transient validation support if needed)

Requirements (exact task wording):
- In the cart (POST /api/v1/cart, PUT /api/v1/cart/{code} and POST /api/v1/cart/{code}/multi):
- A line's quantity must be at least the product's minPerCart, at most its maxPerCart, and a multiple of its packSize. Removing a line (quantity 0) is always allowed.
- A cart may hold at most maxLines different products and maxUnits units in all.
- A change that breaks a rule is refused with HTTP 400 Bad Request and the rule's name as the error's "errorCode": MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES or MAX_UNITS. A refused change changes nothing in the cart, including the other lines of a multi request.
- Product limits are checked for the lines a change adds or changes. The store's caps are checked only when a change adds a line (maxLines) or adds units (maxUnits). So a cart that breaks a rule set later can still be changed to fix it.

Implement validation before mutating/deleting persisted items; multi requests must stage all resulting quantities and commit only after every check passes. Expose a typed exception carrying errorCode so Part 3 can map it to HTTP 400.

Rely on Part 1's Product limit accessors/service and store CartRules service. Part 3 will map your validation exception and serialize warnings.
