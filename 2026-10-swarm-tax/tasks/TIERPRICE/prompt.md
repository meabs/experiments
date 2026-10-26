Wholesale buyers want a lower unit price when they buy more of a product. Add quantity price tiers: each store's admins set them per product, and the cart prices each line by the tier its quantity reaches.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PUT /api/v1/private/product/{id}/tiers replaces all of the product's tiers with the JSON list in the body, and returns HTTP 200 with the stored tiers. An empty list removes them all.
- GET /api/v1/private/product/{id}/tiers returns the product's tiers.
- A tier is JSON: {"minQuantity": 10, "price": 90.00}. Tiers are always returned as a list ordered by minQuantity, lowest first.
- An unknown product, or one that belongs to another store, gives HTTP 404 Not Found.

Rules:

- minQuantity is a whole number of at least 2; price is more than 0. A missing minQuantity or price, a minQuantity that is not a whole number, two tiers with the same minQuantity, or more than 10 tiers gives HTTP 400 Bad Request.
- A tier for more units must have a lower price than every tier for fewer units; otherwise HTTP 400 Bad Request.
- A rejected request changes nothing: the product keeps the tiers it had.
- In a cart, a line's unit price is the price of the tier with the largest minQuantity that the line's quantity reaches. If no tier is reached, or the product's own price (including any special price) is lower than the tier's, the product's own price applies.
- The cart, whenever it is returned, shows each line's "subTotal" (unit price × quantity), and the cart's "subtotal" and "total", at these prices. They are worked out again every time: changing a line's quantity, or changing the product's tiers, reprices carts that already hold it.
- Each line is priced only on its own product's tiers.
- A product with tiers can still be deleted as before.
