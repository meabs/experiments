# Part 2 — private tier REST API

Read `TASK.md` first. Add the protected `/api/v1/private/product/{id}/tiers` GET and PUT endpoints, following the existing private product API conventions for store injection and authorization.

Own these files:

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/**` (add the tier controller/DTO here or extend the existing ProductApi).
- Any tier request/response DTOs under `sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/**`.

PUT accepts a JSON list, validates via the Part 1 tier service, replaces atomically, and returns HTTP 200 with the ordered stored list. GET returns the ordered list. Map malformed/missing/duplicate/limit/order validation to HTTP 400 and unknown or cross-store products to HTTP 404 without mutating old tiers. Match the established exception/status handling and JSON shape (`minQuantity`, `price`).

Rely on Part 1's injectable tier service and its store-constrained product lookup/replacement methods. Do not change cart or core pricing code owned by Part 3.
