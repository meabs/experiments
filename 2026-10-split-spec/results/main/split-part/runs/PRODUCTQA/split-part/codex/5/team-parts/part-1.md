Part 1 — persistence and business service

Own only these files (create the question-specific files under these modules; do not edit shop HTTP/API files):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/**`
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/**`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/**`

Implement the durable product-question entity, status enum, repository, and service. The service must support creating a pending question, finding by id, listing by store/status oldest-first, listing a customer’s questions newest-first, listing published questions for a SKU most-recently-answered-first, answering, rejecting, validation, and the pending-count rule. Associate questions with product/SKU, merchant store, and customer so product deletion can cascade/remove its questions (adapt existing product deletion integration only if it is required and remains within these business/persistence files).

Requirements copied from TASK.md:

“A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}."

“GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first.”

“PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.”

“PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”

“Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.”

Part 2 will consume the service’s public methods and model getters/setters; expose a stable service API such as `createQuestion`, `findById`, `listByStoreAndStatus`, `listByCustomer`, `listPublishedBySku`, `answer`, and `reject` (names may vary, but communicate any deviation in code/API signatures). Part 3 will use the same methods for admin operations.
