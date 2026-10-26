## Part 3 — cart enforcement and warnings

Read `TASK.md` first. Own cart mutation enforcement for POST `/api/v1/cart`, PUT `/api/v1/cart/{code}`, and POST `/api/v1/cart/{code}/multi`, plus the returned cart warning field. Validate product min/max/pack rules and store max-lines/max-units rules transactionally before persisting; rejected single or multi changes must leave the cart unchanged and expose the rule name as `errorCode` in HTTP 400. Apply the specified nuance that store caps are checked only when adding a line or increasing units, while product rules apply to changed/added lines and quantity 0 removes unconditionally.

Owned files (and new files under these modules/packages):

- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/shoppingCart/**` (facade and related cart controller support)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/shoppingCart/ShoppingCartApi.java`
- `sm-shop/src/main/java/com/salesmanager/shop/mapper/cart/**` and cart populators when needed for warnings
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/shoppingcart/**` for `limitWarnings` DTO fields/types
- cart-related exception/error DTO additions in shop API packages when needed

Call the Part 1 contracts to obtain product limits and store caps. Preserve existing cart behavior/statuses except rule violations, which must be HTTP 400 with one of `MIN_PER_CART`, `MAX_PER_CART`, `PACK_SIZE`, `MAX_LINES`, `MAX_UNITS`. Ensure warning computation runs whenever a cart is returned, including carts that violate rules configured later; warning entries use SKU for product rules and null SKU for store caps.
