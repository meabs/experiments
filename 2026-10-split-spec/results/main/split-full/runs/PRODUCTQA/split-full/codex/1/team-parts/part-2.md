## Part 2: customer and public question APIs

Read `TASK.md` first, then this file. Own the customer-facing and anonymous product-question HTTP surface plus its DTOs. Add endpoints under `/api/v1/auth/products/{sku}/questions`, `/api/v1/auth/customer/questions`, and `/api/v1/products/{sku}/questions`, with the exact JSON shapes, status codes, trimming/length validation, authentication behavior, SKU 404 handling, ordering, and public filtering required by `TASK.md`.

Files owned (create or edit only these, plus narrowly required package-local test files):
- `sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/question/**` (request/response/list DTOs)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionApi.java` (new controller, or an equivalent new customer/public controller in this package)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/CustomerQuestionApi.java` (only if you split controllers)

Use the Part 1 question service and existing `ProductService`/`CustomerFacade` patterns. Resolve the authenticated customer from the request principal exactly as existing `/auth/customer/*` APIs do, and ensure unauthenticated calls are rejected by the existing security conventions. Return the complete question JSON for customer endpoints and the reduced published shape/count wrapper for public GET. Do not implement admin endpoints or modify persistence classes.
