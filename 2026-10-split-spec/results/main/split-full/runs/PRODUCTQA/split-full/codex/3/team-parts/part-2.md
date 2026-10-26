Part 2 owns customer-authenticated and public question HTTP APIs. Read TASK.md first.

Own these files (create or modify only these, plus narrowly required package-local support files):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionApi.java (or the equivalent single controller for customer/public product-question routes)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/CustomerQuestionApi.java (if you split routes; avoid duplicate mappings)

Implement POST /api/v1/auth/products/{sku}/questions, GET /api/v1/auth/customer/questions, and GET /api/v1/products/{sku}/questions. Use the existing request principal/customer facade, MerchantStore argument resolver, and exception conventions so no customer token is refused like other /auth routes and public reads need no login. Return 201/200 and exact JSON shapes, propagate the service's validation/not-found errors as 400/404, and preserve required ordering. Consume Part 1's ProductQuestionService and DTOs; do not implement persistence or admin endpoints.

Part 1 provides the service and DTO method names. Part 3 owns admin controller mappings, so avoid /private/questions routes.
