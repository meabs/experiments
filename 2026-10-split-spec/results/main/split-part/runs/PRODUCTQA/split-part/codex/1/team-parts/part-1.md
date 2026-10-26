Implement the product-question domain and persistence/service layer.

Own only these files/areas (create files as needed):
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/question/**
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/question/**
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/question/**
- sm-core-model Product mapping/deletion-related files only where required to cascade question removal with product deletion.

Requirements from TASK.md that apply (exact wording):
- “Shoppers want to ask questions about a product before they buy, and see other shoppers' questions with the store's answers. Add product questions: logged-in customers ask, the store's admins answer or reject them, and anyone can read the answered ones.”
- “A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.”
- “Rules:

- Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.
- A customer can have at most 3 questions waiting for an answer (PENDING) at a time; another gives HTTP 400 Bad Request.
- An unknown sku gives HTTP 404 Not Found (for asking and for the public list); an unknown question id gives HTTP 404 Not Found.
- A rejected question cannot be answered: HTTP 409 Conflict.
- A product with questions can still be deleted as before, and its questions go with it.”

Provide stable service methods for the API parts, including create/ask, find customer questions, find by sku and status, answer, reject, and find by id. Use a status enum with PENDING, PUBLISHED, REJECTED and preserve ordering via service/repository methods. Expose enough fields for API mapping (product SKU, billing first name, timestamps).

Other parts provide/consume:
- Part 2 supplies request/response DTOs and customer/public controllers; it consumes your question service methods.
- Part 3 supplies the admin controller; it consumes your question service methods.
- Keep public method/class names clear and documented in interfaces so the controllers can wire them without editing your files.

Run focused Maven compilation/tests for sm-core-model, sm-core, and dependent modules as useful.
