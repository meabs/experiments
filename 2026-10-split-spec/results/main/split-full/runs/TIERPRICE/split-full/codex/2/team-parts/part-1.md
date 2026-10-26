# Part 1 — product tier domain and persistence

Read `TASK.md` first. Own the product-domain/core persistence layer for quantity tiers. Add the tier representation and wire it to `Product` so tiers are stored per product and survive normal product saves/deletes. Add any core service/repository methods needed by the API and cart, with clear public methods for replacing and reading tiers (for example `getTiers`, `replaceTiers`, or equivalent). Enforce the full validation/ordering rules here or in a reusable core validator, and make replacement atomic so invalid input cannot alter existing tiers. Preserve store ownership checks through the existing `ProductService` contract.

Files owned: `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/**` (including new tier model), and `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**` plus directly associated repository files under `sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/**` if required. Do not edit shop API or cart mapper/calculation files.

Other parts provide: Part 2 will call the core product/tier methods and expose JSON; Part 3 will read tiers from the product/core service while calculating cart prices. Keep method names/public types straightforward and document any assumptions in code.
