# Part 3 — admin API

## Scope
Implement protected store-admin endpoints for listing, answering, and rejecting questions. Match existing `/api/v1/private` authentication and `?store=` resolution. Use only the domain service/DTOs supplied by part 1.

## Files owned
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/question/ProductQuestionAdminApi.java` (or a clearly equivalent private/admin controller)
- Any tests added specifically for these admin endpoints under `sm-shop/src/test/**`

Do not edit part 1 domain/service files or part 2 customer/public controller files.

## Requirements (exact task wording)
Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.

## Relies on part 1
Use `ProductQuestionService`, `ProductQuestionStatus` (`PENDING`, `PUBLISHED`, `REJECTED`), and the full question DTO whose JSON includes id, sku, text, status, answer, askedBy, askedAt, answeredAt. The service must scope every admin operation to the supplied `MerchantStore` and implement conflict/validation rules.
