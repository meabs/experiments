Part 2 — protected admin REST API

Read TASK.md first, then this part file. Implement the private v1 endpoints for product limits and store cart rules, following the existing /api/v1/private controller/security/store conventions. Add PUT/GET /api/v1/private/product/{id}/limits and PUT/GET /api/v1/private/cart-rules, accepting/returning JSON with nullable integer fields exactly as specified. Resolve the MerchantStore from ?store= as existing APIs do; reject unknown/cross-store products with 404. Return 400 for invalid values or cross-field combinations while preserving old values. Setting all product fields null removes limits; null cart-rule fields mean no cap.

Files owned: new admin controller(s), request/response DTOs, and API-specific exception/validation glue under sm-shop and/or sm-shop-model as needed. Do not edit Product/MerchantStore persistence or service implementation files owned by Part 1, and do not edit cart facade/mapper/ShoppingCartApi files owned by Part 3. Call the Part 1 service APIs (record their actual class/method names in your code) rather than duplicating persistence logic.

Part 1 provides persisted product-limit and store-rule services. Part 3 provides cart enforcement and warning behavior independently; your endpoints only configure/read rules.
