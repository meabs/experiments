# CUSTOMERCART: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **Carts are never linked to the logged-in customer.** The cart endpoints (`/api/v1/cart/...`) are public paths,
   and the token filter only authenticates `/api/v1/auth` and `/api/v1/private`, so the customer's token on a cart
   request is never read (probe: `"customer": null`, and `GET /api/v1/auth/customer/cart` finds nothing).
2. **The "current cart" is an arbitrary one.** `ShoppingCartServiceImpl.getShoppingCart` takes the first of the
   customer's carts from a query that joins line items (one row per line), not the most recent.
3. **The logged-in total fails.** `OrderTotalApi` (`/auth/cart/{id}/total`) needs the cart's customer id (cause 1),
   and then prices a cart whose lines were never populated with prices (null item price, HTTP 503).
4. **Logged-in checkout turns every error into a 503**, including the amount mismatch guest checkout reports as a
   400 naming the right amount.
5. **The customer's order list never reports its counts.** The private `OrderFacadeImpl.getReadableOrderList` sets
   `recordsTotal` on one object and returns another built by `populateOrderList` (counts 0), and returns null when
   the customer has no orders.

Three hidden tests (no cart gives 404, a customer never gets another's cart, orders list only their own, newest
first) pass on the unchanged code: they guard behaviour the change must keep.
