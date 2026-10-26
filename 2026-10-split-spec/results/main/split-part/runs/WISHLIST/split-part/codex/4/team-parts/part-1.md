Part 1 — wishlist persistence and domain service

Implement the wishlist domain, persistence, DTO-independent service API, and product-deletion cleanup. Own only files under sm-core-model/src/main/java/com/salesmanager/core/model/wishlist/, sm-core/src/main/java/com/salesmanager/core/business/{repositories,services}/wishlist/, plus any required repository/service wiring files and sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java. Do not edit sm-shop API files.

Requirements (exact task wording):
- "Each customer sees and changes only their own wishlist."
- "A wishlist holds at most 50 products; adding another gives HTTP 400 Bad Request."
- "A missing \"product\" gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found."
- "When a product is deleted, it leaves every wishlist (and the popular report), and deleting it works as before."
- "The wishlist is JSON: {\"count\": 2, \"items\": [{\"sku\": \"...\", \"name\": \"...\", \"price\": 125.00, \"available\": true, \"addedAt\": \"...\"}]}, the most recently added first. \"name\" is the product's name, \"price\" its current price, \"addedAt\" when it was added, and \"available\" is true when the product is available and has stock."
- Admin aggregation needs count "number of customers who have the product on their wishlist".

Provide a Spring service with methods the other parts can call (use clear names/signatures): add(customer, store, sku), get(customer, store), remove(customer, store, sku), move/remove lookup support, and popular(store, limit). Expose enough exception distinctions for 400/404/409 mapping. Persist customer, store, product, and addedAt; enforce newest-first and 50-item limit; ignore duplicate adds without changing timestamp. Other parts provide the authenticated customer/principal, cart integration, and HTTP controllers.
