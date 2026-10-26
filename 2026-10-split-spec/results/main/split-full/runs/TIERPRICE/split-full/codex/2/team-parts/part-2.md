# Part 2 — admin tiers API

Read `TASK.md` first. Implement `PUT /api/v1/private/product/{id}/tiers` and `GET /api/v1/private/product/{id}/tiers`, protected and store-scoped exactly like existing v1 private product APIs. Add request/response DTO(s), JSON binding, status handling, and validation/error mapping. Unknown products or products belonging to another store must be 404; malformed/invalid tier lists must be 400; failed PUTs must leave existing tiers unchanged. GET/PUT responses must be ordered by `minQuantity` ascending.

Files owned: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/**` (prefer a new controller class), and new tier DTO/model files under `sm-shop/src/main/java/com/salesmanager/shop/model/**` as needed. Do not edit core product model/service or cart calculation/mapper files.

Other parts provide: Part 1 supplies the persistent tier type and product-scoped read/replace methods plus validation semantics. Part 3 independently updates cart pricing and response totals; rely only on Part 1’s public methods/types.
