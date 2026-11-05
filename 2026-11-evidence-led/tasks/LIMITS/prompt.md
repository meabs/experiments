Products have a minimum and a maximum order quantity ("quantityOrderMinimum" and "quantityOrderMaximum" in the product API), but the shop ignores them. Whatever a merchant sends when creating or editing a product, the product comes back with 1 and 1, and carts accept any quantity. Merchants need these limits: some products only sell in at least 2, and launch products are limited to a few per customer.

Make the limits work:

- Creating a product (POST /api/v1/private/product) or replacing it (PUT /api/v1/private/product/{id}) stores the "quantityOrderMinimum" and "quantityOrderMaximum" sent, and GET /api/v2/product/{sku} shows them. A product sent without them has a minimum of 1 and no maximum, which the API shows as a maximum of -1. A minimum below 1, or a maximum that is neither -1 nor at least the minimum, gives HTTP 400 Bad Request and nothing is stored.
- A cart can't hold a product in a quantity below its minimum or above its maximum. A cart change that would do that gives HTTP 400 Bad Request and leaves the cart as it was: creating a cart (POST /api/v1/cart/), changing one product's quantity (PUT /api/v1/cart/{code}) or several at once (POST /api/v1/cart/{code}/multi, where either every change is made or none is). A quantity of 0 still removes a product.
- If a product's limits change after it was put in a cart, the cart keeps its quantity, and checkout (POST /api/v1/cart/{code}/checkout) refuses a cart that breaks any product's current limits, with HTTP 409 Conflict: no order is created and nothing else changes. A cart within the limits checks out as before.
- Products whose limits the merchant never set must keep working exactly as before: any quantity from 1 up, as stock allows today.

When you have finished, reply with one short paragraph saying what you changed.
