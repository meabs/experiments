# Part 3 — protected admin API

## Scope and owned files

Own the administrator question-management HTTP layer only. You may add or modify files under:

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` for the admin question controller (keep it separate from Part 2's customer/public controller)
- `sm-shop/src/test/**` for admin endpoint tests, if useful

Do not edit core domain/service/repository files (Part 1) or customer/public DTO/controllers (Part 2). Follow existing `/api/v1/private` admin protection and `?store=` merchant-store resolution patterns.

## Requirements copied from TASK.md

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.

The admin API returns the same full question JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.

## Dependencies from Part 1 / integration notes

Use Part 1's service methods for store/status listing, answer, and reject; pass the resolved `MerchantStore`. Map invalid status and validation to 400, missing IDs to 404, and rejected-answer conflict to 409. The service should return the DTO-ready question object so this controller can serialize the exact fields without changing customer/public behavior.
