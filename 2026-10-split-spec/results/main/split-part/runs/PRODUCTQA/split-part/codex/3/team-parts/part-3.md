## Part 3 — public and admin APIs

Implement public and merchant-admin endpoints in a new or existing API class under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/` or the appropriate v1 package. Own only those public/admin API files and any admin/public response/request DTO files under `sm-shop/src/main/java/com/salesmanager/shop/model/`; do not edit Part 1 service/model or Part 2 customer API files. Use existing `/api/v1/private` authentication and `?store=` merchant-store binding conventions.

Requirements from TASK.md that apply (exact wording):

- “Public API (no login):”
- “GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.”
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.”
- “PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.”
- “PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”
- “Rules: - Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request. - An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found. - A rejected question cannot be answered: HTTP 409 Conflict.”

Rely on Part 1’s service methods for store scoping, status filtering/order, public-only PUBLISHED filtering, answer/reject transitions, validation, and domain errors. Part 2 provides the authenticated customer endpoints and shared full-question representation; use the same field names and timestamp serialization for admin responses, while public responses omit sku/status and include only the specified fields.
