## Part 1: question persistence, domain service, and API models

Implement the product-question domain and service layer. Own only files under `sm-core-model/src/main/java/com/salesmanager/core/model/productquestion/**`, `sm-core/src/main/java/com/salesmanager/core/business/repositories/productquestion/**`, `sm-core/src/main/java/com/salesmanager/core/business/services/productquestion/**`, and new/changed question DTO/model files under `sm-shop-model/src/main/java/com/salesmanager/shop/model/productquestion/**` (plus the minimum Spring XML/JPA mapping file needed to register these classes). Do not edit controller files.

Requirements copied from TASK.md:

- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.
- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.
- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.
- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.

Provide a service with clear methods for create-by-sku/customer, list-by-customer, list-by-store/status, list-published-by-sku, answer, and reject. Preserve store scoping and customer billing first name. Expose status as PENDING/PUBLISHED/REJECTED and timestamps suitable for Jackson ISO output. API parts rely on these service methods and DTOs.
