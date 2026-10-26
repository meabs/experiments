## Part 3: admin/private HTTP API

Implement only new/changed admin controller files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` for product questions (prefer a dedicated questions package/class). Do not edit persistence/service files or customer/public question controllers.

Requirements copied from TASK.md:

- Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):
- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.
- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.

Use the existing private endpoint security conventions and `@ApiIgnore MerchantStore` resolver. Validate status and answer, preserve store isolation, and consume Part 1's service/DTO methods. Do not edit customer/public controllers.
