Part 1 — tier domain, persistence, and service

Implement the quantity-tier data model and a reusable service used by the admin API and cart code. Own only files under sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/**, sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/**, and sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/** (plus migration/schema resources if required by this project). Do not edit controllers or cart classes.

Requirements (exact task wording):
- “Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.”
- “A tier is JSON: {\"minQuantity\": 10, \"price\": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.”
- “Rules:

  - minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
  - A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
  - A rejected request changes nothing: the product keeps the tiers it had.”
- “An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.” (Expose store-scoped lookup suitable for the API.)
- “A product with tiers can still be deleted as before.” Ensure mappings/cascades do not break deletion.

Provide clear public class/method names for the other parts, preferably ProductTier (entity), ProductTierService, and methods such as getTiers(product, store), replaceTiers(product, store, tiers), and priceForQuantity(product, quantity, ownPrice). Validate atomically before replacing and return sorted tiers. The API part will translate request DTOs to this service; the cart part will call the pricing helper on every recalculation.
