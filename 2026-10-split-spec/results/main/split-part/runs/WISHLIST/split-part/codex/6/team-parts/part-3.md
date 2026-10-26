Part 3 — protected admin popular-wishlist report

Add the merchant/private API endpoint for the popular report. Own only files under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1 (a new wishlists/admin controller or focused private API file) and any narrowly scoped API response DTO files under sm-shop/src/main/java/com/salesmanager/shop/model/wishlist. Do not edit customer API, domain, repository, or service files.

Requirements applying to this part (exact task wording):

- Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):
- GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {"sku": "...", "count": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.
- When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.

Follow the authorization and MerchantStore injection pattern used by existing /api/v1/private controllers; the service must scope results to the injected store (the ?store= query selection). Return JSON with exactly sku and count fields and preserve ordering from Part 1's service.

Part 1 provides popular(store) and the response projection. Part 2 is independent except that both use the same wishlist service and DTO package.
