Part 3 — admin API

Own only new/updated files for the admin question HTTP API, preferably:

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionAdminApi.java` (or another clearly admin-only API file)

Do not edit Part 1 persistence/service files or Part 2 customer/public API/DTO files. Use the existing `/api/v1/private/**` security conventions and `@ApiIgnore MerchantStore` resolution, including the `?store=` store context. Serialize the shared full question JSON shape. Map invalid status/validation to 400, missing ids to 404, rejected-answer conflict to 409.

Requirements copied from TASK.md:

“Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”

“A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.“

“Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.”

Part 1 provides service methods `listByStoreAndStatus`, `findById`, `answer`, and `reject` (or equivalents) and the status enum. Part 2 provides any shared DTO/mapper; if no shared mapper is practical, keep admin serialization locally but preserve the exact field names/types.
