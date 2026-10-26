## Part 2 — authenticated customer API

Implement the customer-facing endpoints in `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/customer/` and/or a new product-question API class in `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/` (own only those customer API files and any customer-facing DTO files under `sm-shop/src/main/java/com/salesmanager/shop/model/`). Do not edit the service/model files owned by Part 1 or the admin/public API files owned by Part 3. Follow existing `/api/v1/auth` authentication conventions so a missing/invalid customer token is refused.

Requirements from TASK.md that apply (exact wording):

- “Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):”
- “POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.”
- “GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.”
- “A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.”
- “Rules: - Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request. - A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request. - An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.”

Rely on Part 1’s question service methods for SKU lookup, customer ownership, newest-first ordering, billing first-name projection, validation, and errors. Part 3 independently exposes the public/admin endpoints and relies on the same service and shared question JSON shape.
