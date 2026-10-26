Implement the protected store-admin product-question API.

Own these files (create them as needed):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionAdminApi.java (or another exclusively admin controller file in that package)

Provide GET /api/v1/private/questions?status=..., PUT /api/v1/private/questions/{id}/answer, and PUT /api/v1/private/questions/{id}/reject. Match TASK.md status validation/default, store query scoping, ordering, response shapes, HTTP 400/404/409 behavior, and existing private-endpoint authorization conventions. Use ProductQuestionService and DTOs from part 1/2; do not edit their owned files unless compilation absolutely requires a narrowly scoped compatibility adjustment.
