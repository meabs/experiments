Part 3 — protected popular-wishlists admin API

Own sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/admin/WishlistAdminApi.java (or the closest existing private/admin API package), plus any admin-only DTO classes under sm-shop/src/main/java/com/salesmanager/shop/model/. Do not edit customer API, cart, or core wishlist files.

Requirements (exact task wording):
- "Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):"
- "GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries."

Use the repository/service aggregation supplied by Part 1 (popular(store, 10)); rely on existing private endpoint authorization conventions and MerchantStore resolver from ?store=. Return JSON list with exactly sku and count, sorted and capped as required. Do not weaken authentication.
