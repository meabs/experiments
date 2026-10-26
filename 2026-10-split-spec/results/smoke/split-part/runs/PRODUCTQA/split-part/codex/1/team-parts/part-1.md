# Part 1 — product-question domain and service

## Scope and owned files

Own the persistence/domain and business layer only. You may add or modify files under:

- `sm-core-model/src/main/java/com/salesmanager/core/model/**` (new product-question entity/status and any relationship needed for product deletion)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/**` (question repository)
- `sm-core/src/main/java/com/salesmanager/core/business/services/**` (question service and implementation)
- `sm-core/src/test/**` for focused service/repository tests, if useful

Do not edit controller/API, shop DTO, or security files; expose a clear service API for those parts.

## Requirements copied from TASK.md

Shoppers want to ask questions about a product before they buy, and see other shoppers' questions with the store's answers. Add product questions: logged-in customers ask, the store's admins answer or reject them, and anyone can read the answered ones.

A question, as these and the admin API return it, is JSON: `{"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}`.

Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.

## Contract supplied to other parts

Provide a Spring service (for example `ProductQuestionService`) with methods equivalent to:

- create/ask by SKU, customer, merchant store, and text (validates/normalizes and enforces the three-PENDING limit)
- listByCustomer(customerId, store), newest asked first
- listPublicBySku(sku, store), only PUBLISHED and newest answered first
- listByStoreAndStatus(store, status), oldest asked first
- answer(id, answer, store), reject(id, store), and getById(id)

Use domain status values exactly `PENDING`, `PUBLISHED`, `REJECTED`; represent timestamps and billing first name so the API layer can serialize the required JSON. Throw/use existing runtime exception conventions or documented service exceptions that API coders can map to 400/404/409.
