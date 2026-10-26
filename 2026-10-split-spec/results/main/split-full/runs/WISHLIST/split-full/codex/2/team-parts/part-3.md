Part 3 owns the protected merchant/admin popular-wishlists endpoint. Read TASK.md first. Add GET /api/v1/private/wishlists/popular, protected consistently with other private APIs, honoring ?store= resolution supplied by the framework and returning at most 10 entries sorted by count descending then SKU ascending. Map the Part 1 service aggregation to the exact {sku,count} JSON shape and preserve existing error/auth conventions.

Files owned: sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/*/*Wishlist*Admin*.java (choose the existing package convention, or add a dedicated wishlist admin controller), plus only DTO files in sm-shop-model that are exclusively needed by this endpoint. Do not edit customer wishlist controller files or Part 1 core files.

Other parts provide: Part 1 provides the store-level popular aggregation service and result type; existing MerchantStore/Language injection and private endpoint security conventions should be reused.
