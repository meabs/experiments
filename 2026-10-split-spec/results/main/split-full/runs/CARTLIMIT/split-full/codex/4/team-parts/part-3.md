Part 3 — cart enforcement and shopper warnings

Read TASK.md first, then this part file. Enforce product min/max/pack and store maxLines/maxUnits atomically in POST /api/v1/cart, PUT /api/v1/cart/{code}, and POST /api/v1/cart/{code}/multi. A rejected mutation must return HTTP 400 with errorCode MIN_PER_CART, MAX_PER_CART, PACK_SIZE, MAX_LINES, or MAX_UNITS and leave the cart unchanged (including all multi items). Product rules apply to added/changed lines; store caps apply only when adding a line or adding units, while removals/reductions can repair an already-invalid cart. Quantity 0 removal always succeeds. Add limitWarnings to every returned readable cart, listing sku/rule and null sku for store caps.

Files owned: shopping-cart facade implementation/interface as needed, ShoppingCartApi exception/status handling, cart readable DTO(s), cart mapper/populator and any cart-specific support classes/tests under sm-shop/sm-shop-model. Do not edit Part 1 persistence/service files or Part 2 admin controller/DTO files. Use the Part 1 read APIs for product/store rules; keep validation before mutating/persisting, and ensure multi requests stage changes then commit only on success.

Part 1 supplies persisted rule services and getters. Part 2 supplies only configuration endpoints; no dependency on its controller implementation is required.
