# Part 3: private admin REST API

Read `TASK.md` first, then implement only the store-admin endpoints in a new or existing controller under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1` (prefer a dedicated questions/admin API file). Own any admin-only web DTOs in `sm-shop/src/main/java/com/salesmanager/shop/model` only if needed, coordinating with Part 2 to avoid duplicate classes.

Implement GET `/api/v1/private/questions?status=...` with default PENDING and strict status validation (400 for any other value), PUT `/api/v1/private/questions/{id}/answer` (trim/validate answer, publish, replace existing answer), and PUT `/api/v1/private/questions/{id}/reject`. Use existing private-admin protection, `?store=` resolution, `@ApiIgnore MerchantStore`, and error conventions. Call Part 1's service methods (`findByStoreAndStatus`, `answer`, `reject`, lookup by id) and return the exact question JSON; propagate 404 unknown IDs, 400 validation/status errors, and 409 for answering rejected questions.

Part 1 supplies persistence/service and shared question model; Part 2 supplies customer/public APIs. Do not edit their controllers or core files.
