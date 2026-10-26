# Part 2: private admin HTTP API

Read `TASK.md` first. Implement the protected `/api/v1/private/product/{id}/tiers` GET and PUT endpoints, store scoping, DTO mapping, ordering, and HTTP 404/400/200 behavior. Validate malformed/missing fields, non-whole quantities, duplicates, limits, and tier price ordering; rejected PUTs must not mutate persisted tiers. Follow existing private API security/store injection and exception conventions.

Files owned: `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/**` (new tier API/controller), `sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/**` (new request/read DTOs), and `sm-shop/src/main/java/com/salesmanager/shop/store/controller/product/**` only for a narrowly scoped tier facade if needed. You may add API tests under `sm-shop/src/test`.

Other parts provide/consume: Part 1 supplies the tier domain/service methods, including store-scoped product lookup and replacement validation. Part 3 is independent of HTTP and only relies on tiers being available on the core Product/service.
