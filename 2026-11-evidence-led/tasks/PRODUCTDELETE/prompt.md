Merchants delete discontinued products all the time, and every time they do, something breaks. A cart that held the product can't be opened any more, and an order that included it can't be read by the merchant or by the customer who placed it.

Deleting a product (DELETE /api/v1/private/product/{id}) must not break carts or orders:

- Carts that held the product: GET /api/v1/cart/{code} returns the cart without it, with its subtotal, total and quantity worked out from the products left. A cart whose only product was deleted is returned with no products and a total of 0. The cart can still be changed (PUT /api/v1/cart/{code}, POST /api/v1/cart/{code}/multi) and checked out; the deleted product is never ordered or charged. Trying to add the deleted product to a cart gives HTTP 404 Not Found.
- Orders that included the product: GET /api/v1/private/orders/{id}, GET /api/v1/private/orders, GET /api/v1/auth/orders/{id} and GET /api/v1/auth/orders keep working, and show the product as it was bought: its sku, name, ordered quantity, price and subtotal, exactly as before it was deleted. The order's totals don't change. The order's status can still be changed (PUT /api/v1/private/orders/{id}/status).
- Checkout keeps working for every cart, whatever products have been deleted before.
- GET /api/v2/product/{sku} for a deleted product gives HTTP 404 Not Found. Deleting a product changes nothing about any other product.

When you have finished, reply with one short paragraph saying what you changed.
