Part 1 — core product-question model and service

Own these files (and only these files, except for narrowly required package-local additions):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/** (new entity/status classes)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/** (new Spring Data repository)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/** (service interface/implementation)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java (only the product-delete hook needed to remove questions)

Implement every applicable requirement in the task, exactly:
- “A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.”
- “A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.”
- “An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.”
- “A rejected question cannot be answered: HTTP 409 Conflict.”
- “A product with questions can still be deleted as before, and its questions go with it.”
- Support statuses PENDING, PUBLISHED and REJECTED, with answer/reject transitions and timestamps needed by the APIs.

Provide a service with clear methods the API parts can call (names may follow existing conventions, but include equivalents of): ask by sku/customer/store; list by customer newest first; list by store/status oldest first; list published by sku newest answered first; answer; reject; find by id. Expose the entity fields needed to build the exact JSON, including billing first name and asked/answered timestamps. Enforce trimming/length and pending-limit rules in the service and use repository queries for store/customer/status/order. Make the question entity related to Product and Customer so deleting a Product can cascade/remove its questions; if explicit delete is safer, do it in the ProductServiceImpl hook.

Other parts provide:
- Part 2 supplies customer/public DTOs and controllers and will call your service methods.
- Part 3 supplies admin DTO/controller and will call your service methods.
- Keep method signatures and status/exception behavior straightforward for those callers; use existing shop exception types only in the API layer if needed.
