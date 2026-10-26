Part 1 — tier persistence and domain/service layer

Scope: implement the persistent quantity-tier model and the product-tier service used by the API and cart. Own only files under sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product (including any new tier entity), sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product, and sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product (plus focused tests in the corresponding core modules). Do not edit API or cart files.

Requirements from TASK.md that apply (exact wording):

- A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- Rules:
- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had.
- Each line is priced only on its own product's tiers.
- A product with tiers can still be deleted as before.

Provide stable methods/classes for other parts: a product-scoped tier service that can atomically replace and retrieve tiers for a Product/MerchantStore, and a read method usable by cart pricing to obtain the ordered tiers. Enforce store ownership through the existing ProductService/repository conventions. Preserve existing product deletion behavior via appropriate cascade/orphan handling.

Other parts provide: Part 2 will call your tier service from the private REST controller and map your tier records to JSON; Part 3 will call your ordered read method while recalculating ShoppingCartItem prices.
