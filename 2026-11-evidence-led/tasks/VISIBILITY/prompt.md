Merchants hide products they are still preparing, or have paused, by sending "visible": false. It doesn't work. The flag is used as "available" instead, a hidden product still opens for anyone and still appears in the product lists, and every product reads back as visible. A product created with "available": false comes back available.

Make visibility and availability work, separately:

- Creating a product (POST /api/v1/private/product) or replacing it (PUT /api/v1/private/product/{id}) stores "visible" and "available" as sent, independently of each other.
- For shoppers, a hidden product doesn't exist: GET /api/v2/product/{sku} and GET /api/v2/product/name/{friendlyUrl} give HTTP 404 Not Found, GET /api/v1/products and GET /api/v2/products don't list it, and it can't be added to a cart (HTTP 404). A cart that already holds it when it is hidden can't be checked out (POST /api/v1/cart/{code}/checkout gives HTTP 409 Conflict, and no order is created) until the product is removed from the cart or shown again.
- Merchants still see their hidden products: GET /api/v1/private/products (protected like the other /api/v1/private endpoints) lists all of the store's products, hidden or not, with the same query parameters and response as GET /api/v1/products, each product showing its "visible" flag.
- A visible product shows "visible": true, and "available" as stored. A visible product that is not available is shown with "available": false and can't be added to a cart.
- GET /api/v2/product/name/{friendlyUrl} returns the same product as GET /api/v2/product/{sku}.
- Showing a hidden product again (replacing it with "visible": true) brings it back everywhere, with its stock and price unchanged. Orders that include a product that was hidden later are unaffected.

When you have finished, reply with one short paragraph saying what you changed.
