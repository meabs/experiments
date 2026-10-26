## Part 2 — admin API and request/response DTOs

Read `TASK.md` first. Own the protected `/api/v1/private` administration endpoints and their shop-layer DTOs. Implement product-limit GET/PUT at `/product/{id}/limits` and store cart-rule GET/PUT at `/cart-rules`, using the existing merchant-store resolver and private endpoint conventions, including `?store=` isolation and 404 for missing/cross-store products. Return 200 with the saved nullable values; invalid payloads return 400 and preserve prior values.

Owned files (and new files under these modules/packages):

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` for the new admin controller(s) only
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/**` for limit/cart-rule request and response DTOs only
- API-focused tests under `sm-shop/src/test/**` if useful

Use the domain/service contracts from Part 1 (product lookup/update and store cart-rule get/update). Do not modify persistence/domain classes or the cart facade/mapper/API; Part 1 owns the former and Part 3 owns the latter. Keep error responses compatible with the project’s existing `RestErrorHandler`/constraint handling, with HTTP 400 for validation and HTTP 404 for unknown or foreign products.
