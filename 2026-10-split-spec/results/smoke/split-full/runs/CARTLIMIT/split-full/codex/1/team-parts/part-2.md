Part 2 — admin REST API and request/response DTOs

Read TASK.md first. Own only sm-shop/src/main/java files for the new admin limits/rules endpoints and their request/response DTOs (plus narrowly related API exception/error handling if required). Implement protected /api/v1/private/product/{id}/limits GET/PUT and /api/v1/private/cart-rules GET/PUT using the same store query and authorization conventions as existing private APIs. Return 200 with nullable fields, 404 for unknown/cross-store products, and 400 for invalid combinations while preserving prior values.

Use the model/service methods supplied by Part 1 (product limit access/update and merchant-store cart-rule access/update). Do not modify cart facade/populator/model files owned by Part 3 or persistence files owned by Part 1 unless compilation forces a tiny import-only adjustment.
