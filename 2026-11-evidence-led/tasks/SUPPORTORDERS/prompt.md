Our support team works from the admin order screens and keeps hitting problems:

- When a customer asks us to delete their account (DELETE /api/v1/private/customer/{id}), we can't open their orders afterwards: GET /api/v1/private/orders/{id} gives HTTP 404, and looking up the orders they placed (GET /api/v1/private/orders/customers/{id}) gives HTTP 404 too. We have to keep orders, and answer questions about them, for years after an account is closed.
- The order list (GET /api/v1/private/orders) only ever shows its first page. Asking for any later page returns no orders and a total of 0, so older orders can't be found by browsing.

Fix the order screens:

- An order whose customer account was deleted opens exactly as before (GET /api/v1/private/orders/{id}), with the billing and delivery details and the email it was placed with; it just has no customer. Its status can still be changed, and its history and payment transactions read, as for any order.
- GET /api/v1/private/orders/customers/{id} lists every order placed by that customer id, newest first, whether or not the account still exists, with "recordsTotal" the number of those orders. An id with no orders gives an empty list with "recordsTotal" 0.
- GET /api/v1/private/orders?count={n}&page={p} returns page p (the first page is 0) of the orders matching the request's filters (status, email, name, id), newest first, with "recordsTotal" the number of matching orders and "totalPages" the number of pages of n. A page after the last has no orders but the same totals.
- Registering again with a deleted customer's email creates a new, separate account, which sees none of the old account's orders.

When you have finished, reply with one short paragraph saying what you changed.
