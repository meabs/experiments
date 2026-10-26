# Part 3: protected admin popular-wishlist API

Implement the merchant/admin endpoint and its response DTO only. Own newly created files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/wishlist/**` (or another dedicated admin wishlist package) and any wishlist-specific DTO file not owned by part 2. Do not edit customer API or core service files.

Requirements from TASK.md that apply:

- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”

Use the same controller/security conventions as existing `/api/v1/private` APIs and accept the resolved `MerchantStore` (selected by the `store` query parameter). Return a JSON list, not a wrapper. Ensure ordering and the 10-row cap are guaranteed by the service/query or a deterministic sort before response.

Part 1 provides `WishlistService.popular(MerchantStore)` (or equivalent) returning SKU/count rows and the response projection/DTO if shared. Do not access repositories directly from the controller.
