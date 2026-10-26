# Part 2 — customer and public APIs

Read `TASK.md` first. Own only the customer/public HTTP API layer under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1` (and API-local DTOs/tests if needed). Implement:

- `POST /api/v1/auth/products/{sku}/questions` using the authenticated customer principal, returning 201;
- `GET /api/v1/auth/customer/questions`, newest first, refusing unauthenticated requests consistently with existing `/auth` endpoints;
- `GET /api/v1/products/{sku}/questions`, unauthenticated, returning `{count,items}` and 404 for an unknown SKU.

Use the `ProductQuestionService` and DTOs supplied by Part 1; do not duplicate persistence or business rules. Map validation failures to 400, unknown SKU/question to 404, and preserve exact response JSON and timestamps. Follow existing auth/store resolution conventions (`MerchantStore`, principal, `CustomerFacade`/security) and avoid editing admin controller files owned by Part 3.
