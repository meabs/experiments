Part 3 — admin popular report and product-deletion integration

Own only these files/directories (create new files under them as needed):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/ (admin wishlist/popular API files only)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java (only the deletion integration)
- sm-core/src/main/java/com/salesmanager/core/business/configuration/ (only a focused wishlist deletion listener/config file if you choose that design)

Implement the protected merchant endpoint and ensure deleting a product removes its wishlist entries so the existing deletion operation still succeeds. Follow the authorization style of existing /api/v1/private endpoints and use the ?store= MerchantStore. Return the exact list DTO shape and ordering/limit from the task.

Requirements from TASK.md that apply to this part (exact words):
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”

Part 1 provides the popular aggregation and remove-by-product service methods. The customer API and DTOs are owned by Part 2; avoid editing them. Run focused compilation/tests if practical.
