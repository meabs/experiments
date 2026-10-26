Part 2 — customer and public APIs plus shop DTOs

Own only these files (create new question DTO/API/populator files as needed):

- `sm-shop-model/src/main/java/com/salesmanager/shop/model/**` files specifically for product questions
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` files for customer/public question endpoints (prefer a new `product/ProductQuestionApi.java`)
- `sm-shop/src/main/java/com/salesmanager/shop/populator/**` files specifically for question mapping, if needed

Do not edit Part 1 persistence/service files or Part 3 admin API files. Use `HttpServletRequest.getUserPrincipal()`/existing customer facade patterns so auth endpoints are refused without the customer token. Resolve the logged-in customer and merchant store; pass only service/model objects to Part 1. Return the exact JSON shapes in the task and map validation/not-found/conflict failures to the specified HTTP statuses.

Requirements copied from TASK.md:

“Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):

- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.“

“Public API (no login):

- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.”

“Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.”

Part 1 provides the question model and service methods for create, customer/public listing, and errors. Part 3 provides the admin API independently; both APIs must serialize the shared full question representation consistently.
