Part 2 — customer-authenticated and public HTTP APIs

Own these files (and only these files, except narrowly required package-local additions):
- sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/question/** (request/response DTOs and list wrappers)
- sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/product/ProductQuestionApi.java (or equivalent single customer/public controller)
- Any new mapper/populator under sm-shop/src/main/java/com/salesmanager/shop/populator/** dedicated to question JSON.

Implement these exact task requirements:
- “POST /api/v1/auth/products/{sku}/questions with {"text": "..."} asks a question and returns HTTP 201 with it.”
- “GET /api/v1/auth/customer/questions lists the customer's own questions, whatever their status, newest first.”
- “A question, as these and the admin API return it, is JSON: {"id": 1, "sku": "...", "text": "...", "status": "PENDING", "answer": null, "askedBy": "<the customer's billing first name>", "askedAt": "...", "answeredAt": null}.”
- “Customer API (for the customer logged in with the token from POST /api/v1/customer/login; without a customer's token these are refused like the other /api/v1/auth endpoints)”
- “GET /api/v1/products/{sku}/questions returns the product's published questions: {"count": 1, "items": [{"id": 1, "text": "...", "answer": "...", "askedBy": "...", "answeredAt": "..."}]}, the most recently answered first.”
- “An unknown sku gives HTTP 404 Not Found (for asking and for the public list).”
- “Text and answers are trimmed. A question has 10 to 500 characters; an answer 1 to 2000; otherwise HTTP 400 Bad Request.” (Question validation is also enforced by Part 1 service.)

Use HttpServletRequest principal/customer facade patterns already present so auth is enforced by the existing /auth security chain. Pass MerchantStore (the ?store resolver) into service calls. Return exact field names, nulls, count/items wrapper, and HTTP 201/200/404/400 behavior; do not expose pending/rejected questions publicly.

Other parts provide:
- Part 1 provides the question entity/status and question service methods (ask, customer list, published-by-sku list, etc.).
- Part 3 provides admin endpoints and uses the same DTO/entity mapping conventions; avoid editing its controller file.
