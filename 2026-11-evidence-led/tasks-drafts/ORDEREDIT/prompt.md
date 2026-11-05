Customers often ask to change an order after placing it: one more of something, one fewer of something else, an extra product. Today customer service has to cancel the order and place a new one. Let admins edit an order's products until the order has been delivered.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- PATCH /api/v1/private/orders/{id}/products with {"products": [{"sku": "...", "quantity": 3}], "comment": "..."} sets the quantity of each product listed; "comment" is optional. Products not listed are left as they are. A quantity of 0 removes the product from the order; a sku that is not on the order yet is added. It returns HTTP 200 with {"orderId": 12, "subtotal": 40.00, "tax": 5.20, "total": 45.20, "difference": -11.30}, where "difference" is the new total minus the total before the edit.

Rules:

- An order that does not exist in the store gives HTTP 404 Not Found. Only an order whose status is ORDERED or PROCESSED can be edited; any other status gives HTTP 409 Conflict.
- Every listed sku must be a product of the store, every quantity 0 or more, and the request must list at least one product; otherwise HTTP 400 Bad Request. The same sku listed twice gives HTTP 400. An edit that would leave the order with no products gives HTTP 400.
- Products already on the order keep the unit price the customer paid. A product added by an edit is charged at the price checkout would charge for it today.
- Stock follows the edit: raising a quantity or adding a product takes the extra units from the product's stock, and lowering a quantity or removing a product puts the units back. If any product in the edit doesn't have enough stock for its extra units, the whole edit is rejected with HTTP 409 Conflict and nothing changes.
- After an edit, the order's subtotal, tax and total are worked out again exactly as checkout works them out for this order's customer and delivery address. The order's totals (GET /api/v1/private/orders/{id}) and its products show the edited order, and the response's figures match them.
- The difference is recorded as a payment transaction on the order (GET /api/v1/private/orders/{id}/payment/transactions): CAPTURE for a positive difference, REFUND for a negative one, for the amount of the difference. An edit with no difference records no transaction.
- Every edit adds an entry to the order's status history (GET /api/v1/private/orders/{id}/history), with the order's status, a comment that names each changed product with its old and new quantity, and the edit's comment if one was given.

When you have finished, reply with one short paragraph saying what you changed.
