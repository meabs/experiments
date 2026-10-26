## Part 1 — question data model and service

Implement the persistence/domain and business-service layer for product questions. Own only files under `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/`, `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/`, and `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/` (plus narrowly necessary persistence/config files in those modules). Add the question entity, status enum, repository, service interface/implementation, validation/state rules, ordering/filter queries, and cleanup when a product is deleted. Expose methods that API parts can call by SKU/product/customer/store, including create, customer list, public published list, admin status list, answer, reject, and lookup by id.

Requirements from TASK.md that apply (exact wording):

- “Shoppers want to ask questions about a product before they buy, and see other shoppers' questions with the store's answers. Add product questions: logged-in customers ask, the store's admins answer or reject them, and anyone can read the answered ones.”
- “A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.”
- “The most recently answered first.”
- “GET /api/v1/private/questions?status=PENDING lists the store's questions with that status (PENDING, PUBLISHED or REJECTED; PENDING when not given), oldest asked first.”
- “PUT /api/v1/private/questions/{id}/answer with {"answer": "..."} sets the answer and publishes the question (status PUBLISHED, "answeredAt" set), returning HTTP 200 with it. Answering a published question again replaces its answer.”
- “PUT /api/v1/private/questions/{id}/reject rejects the question (status REJECTED), returning HTTP 200 with it. A rejected question is not shown publicly, even if it had been published.”
- “Rules: - Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request. - A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request. - An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found. - A rejected question cannot be answered: HTTP 409 Conflict. - A product with questions can still be deleted as before, and its questions go with it.”

Other parts provide: Part 2 supplies the authenticated customer id and maps service objects to customer JSON (`ProductQuestion` plus API DTOs/methods). Part 3 supplies merchant store context and maps service objects to admin/public JSON. Keep service methods usable without controller concerns and throw/use clear exceptions for not-found, validation, pending-limit, and rejected-answer cases.
