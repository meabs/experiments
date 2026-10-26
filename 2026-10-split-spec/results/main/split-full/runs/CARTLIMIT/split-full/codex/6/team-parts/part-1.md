## Part 1 — persistence and domain services

Read `TASK.md` first. Own the domain/persistence layer only: add the product limit values and store cart-cap values, plus services/repositories needed to read and update them safely per merchant store. Keep this usable by both the admin API and cart code.

Owned files (and new files under these modules/packages):

- `sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/Product.java`
- `sm-core-model/src/main/java/com/salesmanager/core/model/merchant/MerchantStore.java`
- `sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/**` only where product-limit accessors/service methods are needed
- `sm-core/src/main/java/com/salesmanager/core/business/services/merchant/**` only where cart-rule accessors/service methods are needed
- matching repository interfaces/implementations and any core-model/domain exception classes required for these operations

Expose clear methods for the other parts, e.g. `ProductService.getById(id)`, product limit getters/setters, and merchant-store cart-rule getters/setters (or a dedicated `CartRuleService` with `getForStore`, `updateForStore`). Enforce validation atomically in the domain/service layer: positive whole numbers, min <= max, max >= pack size; reject invalid updates without mutating old values. Ensure product lookup can verify merchant ownership. Do not edit controllers, shop DTOs, or cart facade/API code; those belong to Parts 2 and 3.

Part 2 will call your product/store service methods from admin endpoints. Part 3 will call them while validating cart mutations and generating warnings.
