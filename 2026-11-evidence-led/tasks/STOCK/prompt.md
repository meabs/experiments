Merchants report that stock levels are wrong. When an order is placed, the stock of the products ordered often doesn't go down, and sometimes another product's stock goes down instead. Cancelling an order never gives the stock back. Shoppers can put more in their cart than we have, and can check out orders we can't fill. A product with no stock left is still shown as available.

Make stock right everywhere it is used. "Stock" is the "quantity" that GET /api/v2/product/{sku} shows for a product.

- Checkout (POST /api/v1/cart/{code}/checkout and POST /api/v1/auth/cart/{code}/checkout) takes exactly the ordered quantity from the stock of each product ordered, and changes no other product's stock.
- If any product in the cart has less stock than the cart's quantity of it, checkout is refused with HTTP 409 Conflict: no order is created, no stock changes, and the cart stays as it was.
- A cart change that would leave the cart holding more of a product than its stock is refused with HTTP 409 Conflict and leaves the cart as it was. This applies to creating a cart (POST /api/v1/cart/), changing one product's quantity (PUT /api/v1/cart/{code}) and changing several at once (POST /api/v1/cart/{code}/multi, where either every change is made or none is). A product with no stock can't be added at all (HTTP 409). Lowering a quantity or removing a product is always allowed.
- Setting an order's status to CANCELED (PUT /api/v1/private/orders/{id}/status) puts each ordered product's quantity back into its stock. This happens once: setting CANCELED again on an order that is already canceled changes nothing. A canceled order can't be given any other status (HTTP 409 Conflict, and stock is unchanged). Other status changes don't change stock.
- GET /api/v2/product/{sku} shows "available": false and "canBePurchased": false for a product with no stock, and shows it as available again once it has stock. A product the merchant marked unavailable stays unavailable whatever its stock.

When you have finished, reply with one short paragraph saying what you changed.
