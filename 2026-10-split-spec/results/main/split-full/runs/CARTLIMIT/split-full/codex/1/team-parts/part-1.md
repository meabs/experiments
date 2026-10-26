Part 1 owns the persistence/domain and service layer for purchase limits and store cart rules.

Read TASK.md first. Add the product-limit and merchant-store cart-cap state, persistence mappings/repositories as needed, and a service API that lets callers get/set validated limits for a Product and get/set validated caps for a MerchantStore. Validation must preserve old values on invalid input and support clearing all values with nulls. Expose clear class/method names for the API and cart parts (for example ProductLimitService.get/setLimits and CartRuleService.get/setRules, or an equivalent coherent design).

Owned files: sm-core-model domain entities (including Product/MerchantStore if appropriate), sm-core persistence repositories, service interfaces/implementations and their Spring wiring/configuration. Do not edit REST controllers or cart facade/mapper/model files owned by other parts.

Part 2 will call your service methods from admin REST endpoints; Part 3 will call them from cart validation and warning generation. Keep APIs store-scoped and ensure product lookup rejects products belonging to another store.
