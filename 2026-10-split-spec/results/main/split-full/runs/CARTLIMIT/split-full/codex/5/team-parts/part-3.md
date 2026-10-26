Part 3 owns cart mutation enforcement and warning representation.

Files owned: sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/facade/**; sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java; sm-shop/src/main/java/com/salesmanager/shop/model/shoppingcart/**; sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**; and related cart populator files under sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/**.

Enforce product quantities and store caps atomically for add/modify/multi operations, allowing quantity 0 removal and allowing fixes to carts that already violate newly-set caps. Map violations to HTTP 400 with errorCode MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES, or MAX_UNITS; multi requests must roll back entirely. Add limitWarnings to every returned cart. Consume Part 1's reusable validator/service and limits accessors; do not edit admin product/cart-rules controllers.
