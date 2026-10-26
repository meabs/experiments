Part 3: protected admin question endpoints.

Own files under sm-shop/src/main/java/com/salesmanager/shop/store/api/v1 (create a focused admin question API class), plus only directly necessary API-layer tests.

Implement protected endpoints:
- GET /api/v1/private/questions?status=PENDING (default PENDING; only PENDING/PUBLISHED/REJECTED, invalid status 400; oldest asked first)
- PUT /api/v1/private/questions/{id}/answer with {"answer":"..."} (200; publish/set answeredAt; replacement allowed for published; rejected -> 409)
- PUT /api/v1/private/questions/{id}/reject (200; rejected and hidden publicly)

Follow existing private API protection, MerchantStore from ?store=, request/response conventions, and map unknown IDs to 404 and validation to 400. Consume ProductQuestionService and DTOs from Part 1; do not implement persistence or customer/public endpoints. Ensure store scoping is enforced by service/API lookup.
