## Part 2: private discounts admin API

Read `TASK.md` first, then implement only the admin REST API for discount management.

Files owned (create or modify only these, unless a compile fix is absolutely required):
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/**`
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/**`

Add protected `/api/v1/private/discounts` endpoints: POST (201 and stored id), GET, PUT `/{id}`, DELETE `/{id}`, scoped to the injected `MerchantStore` resolved from `?store=` like neighboring private APIs. Map validation failures to 400, duplicate code conflicts to 409, and missing resources to appropriate 404 responses. Use the Part 1 discount service and DTO/model contract; do not duplicate persistence or cart calculation.

Part 1 provides the discount service and shop model. Part 3 independently handles shopper promo application and cart output. Do not edit Part 1 or Part 3 files.
