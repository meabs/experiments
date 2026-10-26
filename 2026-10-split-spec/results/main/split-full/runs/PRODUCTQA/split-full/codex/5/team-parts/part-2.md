Part 2: customer-authenticated and public question endpoints.

Own these files under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1 (create a focused product/customer question API class or classes in the existing packages), plus only directly necessary API-layer tests.

Implement:
- POST /api/v1/auth/products/{sku}/questions (201)
- GET /api/v1/auth/customer/questions (customer's own questions, newest first)
- GET /api/v1/products/{sku}/questions (public published response with count/items and public fields)

Use the existing customer-token authentication conventions (request Principal and CustomerFacade/customer lookup), MerchantStore resolution, and ProductService lookup. Unauthenticated customer endpoints must be rejected by existing security configuration. Return required 404/400 responses via the project's established exception/response style. Consume the ProductQuestionService and DTOs supplied by Part 1; do not implement persistence or admin endpoints. Keep endpoint JSON exactly aligned with TASK.md.
