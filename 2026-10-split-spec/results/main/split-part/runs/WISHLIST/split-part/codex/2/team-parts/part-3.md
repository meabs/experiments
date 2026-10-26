# Part 3 — protected admin popular-wishlists report

Implement the admin API endpoint and response model for popular wishlisted products. Own files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` (a new admin wishlist API/report file), `sm-shop/src/main/java/com/salesmanager/shop/model/wishlist/**` (admin response DTOs only), and any API wiring/config file needed solely for this endpoint. Do not edit Part 1’s core service/model files or Part 2’s customer endpoint files.

Requirements (exact task wording):

- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/wishlists/popular returns the store's most wished products: a list of {\"sku\": \"...\", \"count\": 3}, where count is the number of customers who have the product on their wishlist. Highest count first, ties by sku in alphabetical order, at most 10 entries.”
- “When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before.”

Follow existing private-controller authorization, `MerchantStore` injection via `?store=`, language/request conventions, and JSON serialization. Return an empty list when no products qualify. The report must count distinct customers’ wishlist membership (not duplicate adds).

Other parts provide: Part 1 provides a service method that aggregates by store and applies count/order/limit; Part 2 provides customer-facing DTO conventions but does not need to be changed for this endpoint. Do not edit customer API files.
