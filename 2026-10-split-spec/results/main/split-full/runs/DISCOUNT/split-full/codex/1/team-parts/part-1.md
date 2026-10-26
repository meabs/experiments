## Part 1: discount domain, persistence, and service

Read `TASK.md` first. Own the discount domain and reusable business service, including persistence and the shop-facing request/response model if needed for the service contract.

Files owned (create or modify only these, unless a compile fix is absolutely required):
- `sm-core-model/src/main/java/com/salesmanager/core/model/discount/**`
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/**`
- `sm-core/src/main/java/com/salesmanager/core/business/services/discount/**`
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/**`

Implement a store-scoped discount entity/enum and service methods for CRUD, case-insensitive uniqueness, validation (type/value/dates/categories), lookup by store/code, and evaluating an applied code against cart items. Expose clear methods the other parts can call, such as `create/update/delete/list`, `findByCode(store, code)`, and an evaluation/calculation method returning applicability and rounded discount. Categories must validate through the existing category service/repository and support descendants. Keep the merchant-written code casing.

Part 2 will call your CRUD service from the admin controller. Part 3 will call your lookup/evaluation methods from cart promo application and cart recalculation. Do not edit those controllers/facades yourself.
