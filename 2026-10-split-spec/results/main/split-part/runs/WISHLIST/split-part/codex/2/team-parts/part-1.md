# Part 1 — wishlist domain and service

Implement the persistent wishlist domain and business service. Own new/changed files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/wishlist/**`, `sm-core/src/main/java/com/salesmanager/core/business/repositories/**` (wishlist repository files only), and `sm-core/src/main/java/com/salesmanager/core/business/services/**` (wishlist service files only). If product deletion requires a small change in the existing product service, that existing product-service file is also owned by this part; coordinate by exposing a cleanup method rather than editing API code.

Requirements (exact task wording):

- “Add a wishlist for logged-in customers, a way to move a wishlist item into a cart, and a report of the store's most wished products.”
- “Each customer sees and changes only their own wishlist.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.”
- “A missing \"product\" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”
- The wishlist representation must support: `{"count": 2, "items": [{"sku": "...", "name": "...", "price": 125.00, "available": true, "addedAt": "..."}]}`, newest first; name/current price/addedAt/availability semantics exactly as stated in TASK.md.
- Popular aggregation must provide each product SKU and customer count, sorted highest count first then SKU alphabetically, limited to 10.

Expose a clear service API for the other parts, for example methods to list/add/remove/move, and a method returning popular products. The customer API part will need an atomic move operation or enough primitives to ensure conflict leaves both cart and wishlist unchanged. The admin API part will call the popular method. Use existing Customer, MerchantStore, Product, availability, and repository conventions.

Other parts provide: Part 2 supplies HTTP customer endpoints and invokes this service plus the existing shopping-cart facade/service; Part 3 supplies the protected admin endpoint and invokes the popular-service method. Do not edit those parts’ files.
