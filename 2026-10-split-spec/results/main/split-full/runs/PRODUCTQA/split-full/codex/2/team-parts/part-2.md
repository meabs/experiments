# Part 2: customer and public REST APIs

Read `TASK.md` first, then implement only the customer-authenticated and public endpoints. Own new or modified files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer` and `.../api/v1/product`, plus request/response web DTOs under `sm-shop/src/main/java/com/salesmanager/shop/model` if those are not placed in Part 1's model package. Do not edit core persistence/service files or admin API files.

Implement POST `/api/v1/auth/products/{sku}/questions` (201), GET `/api/v1/auth/customer/questions` (customer token required), and GET `/api/v1/products/{sku}/questions` (public). Match existing `@ApiIgnore MerchantStore`, customer-security, error-handler, and JSON conventions. Use Part 1's service methods (`askQuestion`, `findByCustomer`, `findPublicBySku`, or their documented equivalents), preserve the exact JSON fields and ordering rules, and map unknown SKU to 404 and validation failures to 400.

Part 1 provides the question service, status, and response/request model. Part 3 independently adds admin endpoints against the same service/model; avoid changing its files.
