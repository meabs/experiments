Part 3 — protected store-admin HTTP API

Own these files (and only these files, except narrowly required package-local additions):
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/private/** only if that package exists; otherwise add sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/question/ProductQuestionAdminApi.java
- Any admin-only question request/response DTO files under sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/question/admin/**.

Implement these exact task requirements:
- “GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first. Any other status gives HTTP 400 Bad Request.”
- “PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.”
- “PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=)”
- “Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.”
- “An unknown question id gives HTTP 404 Not Found.”
- “A rejected question cannot be answered: HTTP 409 Conflict.”

Use existing admin authentication/authorization conventions for /private endpoints and MerchantStore injection. Validate status strictly and scope every query/mutation to the requested store so another store's id is treated as 404. Return the same full question JSON shape as customer/admin requirements. Delegate transition, validation, trimming, and timestamps to Part 1 service methods.

Other parts provide:
- Part 1 provides service methods for list-by-store/status, answer, reject, and find-by-id/store.
- Part 2 provides shared question DTOs/mappers; reuse them rather than duplicate JSON definitions where practical, but do not edit Part 2's controller.
