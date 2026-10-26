Implement the customer-authenticated and public REST API plus shared REST DTOs for product questions.

Own only these files/areas (create files as needed):
- sm-shop-model/src/main/java/com/salesmanager/shop/model/product/question/** (all request/response/list DTOs)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product question/customer question controller files; you may add a dedicated controller under the existing v1 package, but do not edit admin question controller files owned by Part 3.

Requirements from TASK.md that apply (exact wording):
- “Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):

- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.”
- “Public API (no login):

- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.”
- “Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A product with questions can still be deleted as before, and its questions go with it.”

Use the existing auth conventions (HttpServletRequest principal, @ApiIgnore MerchantStore, and /api/v1/auth paths) so missing customer tokens are rejected by the existing filter. Return ResponseEntity/status 201 for creation and map all fields exactly; public responses must omit status/sku and include count/items.

Other parts provide/consume:
- Part 1 provides the question entity/status and question service interface/implementation; call those methods rather than accessing persistence directly.
- Part 3 consumes the DTO classes for admin responses and relies on their JSON shape.

Run relevant Maven compilation/tests for sm-shop-model and sm-shop.
