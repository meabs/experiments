# Part 1 — question model and service

Read `TASK.md` first. Own the persistence/domain layer for product questions, including any core-model entities/enums, shop-model request/response DTOs needed by the APIs, Spring Data repository, service interface/implementation, and product-delete cascade integration. Keep all edits to the model/core modules and their configuration/resources; do not edit API controller files.

Provide a service named `ProductQuestionService` (and implementation bean) with methods sufficient for the controllers:

- ask/create by product SKU, customer, store and trimmed text, enforcing 10–500 chars and max three PENDING questions per customer;
- list a customer's questions newest asked first;
- list a store's questions by status oldest asked first;
- list published questions for a SKU newest answered first;
- answer by id (trimmed 1–2000 chars, publish, set answeredAt; reject answering REJECTED with a domain exception/status the API can map to 409);
- reject by id;
- lookup unknown SKU/question as a not-found condition.

Expose stable DTOs/mapping for the exact JSON fields in `TASK.md` (`id`, `sku`, `text`, `status`, `answer`, `askedBy`, `askedAt`, `answeredAt`) plus a public-list wrapper (`count`, `items`). Use existing `ProductService` and customer/store models. Ensure deleting a product also deletes its questions (cascade or service cleanup).

Other parts rely on the service and DTO class/method names you implement; communicate any exact names in your completion report. Do not modify `sm-shop` API controllers owned by parts 2 or 3.
