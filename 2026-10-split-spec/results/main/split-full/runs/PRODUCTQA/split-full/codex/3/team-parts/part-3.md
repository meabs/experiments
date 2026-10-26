Part 3 owns the protected admin HTTP API. Read TASK.md first.

Own these files (create or modify only these, plus narrowly required package-local support files):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/question/ProductQuestionAdminApi.java (or one equivalent controller dedicated to /private/questions)

Implement GET /api/v1/private/questions?status=..., PUT /api/v1/private/questions/{id}/answer, and PUT /api/v1/private/questions/{id}/reject. Follow existing private endpoint authentication/group/store authorization patterns and MerchantStore (?store=) resolution. Validate status values and answer length/trim, enforce 400/404/409 behavior from TASK.md, ordering, and exact admin question JSON. Answering PUBLISHED replaces its answer; rejected cannot be answered. Consume Part 1's ProductQuestionService and DTOs; do not edit customer/public controller files.

Part 1 provides persistence/service and DTOs. Part 2 owns customer/public routes; avoid duplicate mappings.
