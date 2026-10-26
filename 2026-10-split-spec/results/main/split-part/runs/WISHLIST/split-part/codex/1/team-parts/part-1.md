Part 1 — wishlist persistence and domain service

Own only these files/directories (create new files under them as needed):
- sm-core-model/src/main/java/com/salesmanager/core/model/wishlist/
- sm-core/src/main/java/com/salesmanager/core/business/repositories/wishlist/
- sm-core/src/main/java/com/salesmanager/core/business/services/wishlist/

Implement the persistent customer/store wishlist model, repository queries, and a Spring service usable by the APIs. Keep entries customer-scoped and store-scoped, retain an added timestamp, enforce the 50-product limit and duplicate-idempotency, provide newest-first item retrieval, popular-product aggregation (count distinct customers, highest count first, SKU alphabetical ties, max 10), and operations needed to remove all entries for a deleted product. Resolve product/SKU and current product data through existing product services/repositories as appropriate. Expose clear class/method names for the API coder, including methods for list, add, remove, membership lookup, move preparation/removal, popular aggregation, and product cleanup.

Requirements from TASK.md that apply to this part (exact words):
- “Each customer sees and changes only their own wishlist.”
- “A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”
- “The wishlist is JSON: {\"count\": 2, \"items\": [{\"sku\": \"...\", \"name\": \"...\", \"price\": 125.00, \"available\": true, \"addedAt\": \"...\"}]}, the most recently added first. \"name\" is the product's name, \"price\" its current price, \"addedAt\" when it was added, and \"available\" is true when the product is available and has stock.”
- “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”

Other parts provide/consume: Part 2 calls the service with the authenticated Customer and MerchantStore and needs DTO-ready entry data plus atomic remove-after-cart-success; Part 3 calls popular aggregation and product-delete cleanup. Coordinate only through public service/repository methods, not by editing their files.
