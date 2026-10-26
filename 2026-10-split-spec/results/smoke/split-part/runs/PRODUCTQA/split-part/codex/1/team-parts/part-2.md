# Part 2 — customer and public APIs

## Scope and owned files

Own customer-facing and public HTTP/API representations only. You may add or modify files under:

- `sm-shop-model/src/main/java/com/salesmanager/shop/model/**` (question request/response DTOs and public wrapper)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` for customer/public question endpoints
- `sm-shop/src/test/**` for API-focused tests, if useful

Do not edit core entities/repositories/services (Part 1) or admin question endpoints (Part 3). Reuse the service contract from Part 1 and existing customer authentication patterns (`Principal`, `CustomerFacade`, `@ApiIgnore MerchantStore`).

## Requirements copied from TASK.md

Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):

- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.

Public API (no login):

- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.

## Dependencies from Part 1 / integration notes

Call the Part 1 service methods for ask, customer listing, and public SKU listing; do not duplicate persistence or validation. Resolve the authenticated customer from the request `Principal`/existing `CustomerFacade` and pass the billing first name through the service/entity. Map service errors to the specified HTTP statuses using existing `RestErrorHandler` conventions. Public response must omit SKU/status/id? exactly as specified: each item has id, text, answer, askedBy, answeredAt and wrapper has count/items.
