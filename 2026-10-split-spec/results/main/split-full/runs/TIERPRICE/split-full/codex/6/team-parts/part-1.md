# Part 1 — tier domain and persistence

Read `TASK.md` first. Implement the quantity-tier domain in the core model and a service API that the controller and cart code can use.

Own these files (and only these areas unless a strictly necessary companion file is required):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/**` for the tier value/entity and the Product association/accessors.
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**` and its product repository package for tier persistence/service behavior.

Provide a Spring-injectable service (use a clear name such as `ProductTierService`) with methods equivalent to: get tiers for a product/store, replace tiers atomically after validating all TASK rules, and resolve a product by id constrained to a store. Preserve existing product deletion behavior. Validation failures must leave existing tiers unchanged; unknown/cross-store products must be distinguishable for the API as not found. Keep returned tiers sorted by minQuantity.

Part 2 will call your service methods from the private REST controller. Part 3 will call a method (or an equivalent clearly documented helper) to obtain the current tiers for a Product while calculating cart prices.
