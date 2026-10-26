Part 2 owns the admin REST API and request/response DTOs for product limits and store cart rules.

Read TASK.md first. Then implement PUT and GET /api/v1/private/product/{id}/limits and PUT and GET /api/v1/private/cart-rules, following existing private API conventions and store query resolution. Return 200 and the configured nullable values, 404 for unknown/cross-store products, and 400 for validation failures while leaving prior values unchanged. Use the domain services supplied by Part 1 (their actual names/signatures may be inspected after it starts). Add only DTOs/controllers/supporting API exception handling in your owned areas; do not change persistence/domain or cart mutation code.

Owned files: new/modified sm-shop API v1 controller package files and API model/DTO files needed solely for these endpoints. Part 1 provides store-scoped limit/rule service methods; Part 3 provides cart behavior and warning fields.
