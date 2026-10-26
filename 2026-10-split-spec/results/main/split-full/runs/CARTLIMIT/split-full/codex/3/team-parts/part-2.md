Part 2 owns the admin HTTP API and its DTOs.

Read TASK.md first. Implement protected /api/v1/private endpoints: PUT/GET /product/{id}/limits and PUT/GET /cart-rules, using the same MerchantStore resolution/security conventions as existing private APIs and ?store scoping. Return 200 payloads with nullable fields, 404 for missing/wrong-store products, and 400 for invalid values without mutating old values. Add request/response DTOs and exception/error handling as needed.

Files owned: sm-shop API/controller classes for these endpoints (prefer new focused controller if conventions allow), sm-shop-model DTO classes for limits/rules, and narrowly related API exception/config files. Consume Part 1's core service/domain methods (name them clearly in your implementation); do not edit cart facade/populator/mapper or core model files owned by Part 1.
