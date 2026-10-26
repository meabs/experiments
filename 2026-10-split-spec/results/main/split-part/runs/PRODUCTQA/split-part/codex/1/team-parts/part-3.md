Implement the protected admin REST API for product questions.

Own only these files/areas (create files as needed):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/** question admin controller files (dedicated controller preferred; do not edit Part 2's controller)
- Any admin-only request binding/helper file under sm-shop/src/main/java/.../product/question/** that is not a shared DTO.

Requirements from TASK.md that apply (exact wording):
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.
- PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.
- PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”
- “Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.”

Use the same merchant-store/admin authentication conventions and ?store binding as existing /api/v1/private controllers. Validate status strictly, answer length, unknown IDs, and rejected-answer conflict; return shared Part 2 response DTOs with HTTP 200.

Other parts provide/consume:
- Part 1 provides the question service and domain methods.
- Part 2 provides shared request/response DTO classes and JSON mapping; import/use them without modifying their files.

Run relevant Maven compilation/tests for sm-shop.
