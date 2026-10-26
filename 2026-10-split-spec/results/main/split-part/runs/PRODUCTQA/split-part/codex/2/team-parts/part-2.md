## Part 2: customer-authenticated and public HTTP APIs

Implement only the customer/public controller(s) under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/**` and/or `.../api/v1/product/**` that are needed for product questions. Do not edit persistence/service files or admin/private controller files.

Requirements copied from TASK.md:

- Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):
- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.
- Public API (no login):
- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.
- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list).

Use the existing Principal/request customer lookup and MerchantStore argument resolver so auth behavior matches other `/auth` endpoints. Return the exact status codes and JSON shapes. Consume Part 1's question service and DTOs; do not duplicate persistence logic.
