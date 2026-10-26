Shoppers want to ask questions about a product before they buy, and see other shoppers' questions with the store's answers. Add product questions: logged-in customers ask, the store's admins answer or reject them, and anyone can read the answered ones.

Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints):

- POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.
- GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.
- A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.

Public API (no login):

- GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.
