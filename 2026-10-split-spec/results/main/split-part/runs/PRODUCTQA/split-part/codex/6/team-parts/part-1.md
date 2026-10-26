# Part 1 — question domain model and service

## Scope
Implement the persistent product-question domain and the service layer used by the customer, public, and admin APIs. Add DTOs/response models and mapping helpers if needed so controllers can return the exact JSON shapes. Ensure product deletion cascades to questions.

## Files owned
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/**` (new question entity/status types)
- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java` (only the question relationship)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/**`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/**`
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/catalog/product/question/**`
- `sm-shop/src/main/java/com/salesmanager/shop/populator/catalog/product/question/**` or equivalent question mapper files

## Requirements (exact task wording)
Shoppers want to ask questions about a product before they buy, and see other shoppers' questions with the store's answers. Add product questions: logged-in customers ask, the store's admins answer or reject them, and anyone can read the answered ones.

A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.

## Provides to other parts
Expose a service bean (for example `ProductQuestionService`) with methods to create/find customer questions, list by customer, list by product/status, answer, and reject; expose status values `PENDING`, `PUBLISHED`, `REJECTED`; and expose response/request classes with getters matching the JSON fields. Controllers in parts 2 and 3 should use these methods rather than repositories directly.
