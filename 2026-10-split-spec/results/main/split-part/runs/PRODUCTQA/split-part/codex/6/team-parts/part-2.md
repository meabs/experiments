# Part 2 — customer and public APIs

## Scope
Implement the authenticated customer endpoints and unauthenticated public product-question endpoint. Follow existing `/api/v1/auth` security conventions and use the domain service/DTOs supplied by part 1.

## Files owned
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/ProductQuestionCustomerApi.java` (or a clearly equivalent customer API controller)
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionPublicApi.java` (or a clearly equivalent public API controller)
- Any tests added specifically for these customer/public endpoints under `sm-shop/src/test/**`

Do not edit part 1 domain/service files or part 3 admin controller files.

## Requirements (exact task wording)
Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):

- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.

Public API (no login):

- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.

## Relies on part 1
Use `ProductQuestionService` (or its documented equivalent), `ProductQuestionStatus`, and the question response/list DTOs. Product lookup must be store-aware and the service must enforce trimming, validation, and the three-PENDING limit.
