Customer service handles returns by hand, and the refund endpoint, POST /api/v1/private/orders/{id}/refund, does nothing. Build returns and refunds for orders.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- POST /api/v1/private/orders/{id}/returns records a return and refunds it. The body is {"lines": [{"sku": "...", "quantity": 2}], "restock": true, "reason": "..."}; "reason" is optional. It returns HTTP 201 with the return.
- GET /api/v1/private/orders/{id}/returns lists the order's returns, oldest first.
- POST /api/v1/private/orders/{id}/refund refunds everything on the order that has not been returned yet, as one return with "restock" false and reason "refund", and returns HTTP 201 with that return.
- A return is JSON: {"id": 7, "orderId": 12, "lines": [{"sku": "...", "quantity": 2, "amount": 50.00}], "tax": 6.50, "amount": 56.50, "restocked": true, "reason": "...", "date": "2026-11-04"}. "amount" on a line is what the customer paid for those units; "tax" is the tax refunded; "amount" on the return is the lines plus the tax.

Rules:

- An order that does not exist in the store gives HTTP 404 Not Found. A CANCELED or REFUNDED order cannot be returned or refunded: HTTP 409 Conflict.
- Each line's sku must be a product on the order and its quantity more than 0, and the request must have at least one line; otherwise HTTP 400 Bad Request. Lines with the same sku in one request count together. A product can't be returned more times in total than it was ordered: a request that would go over gives HTTP 400 and records nothing.
- A line's amount is the unit price the customer paid on the order, times the quantity.
- Tax: the order's tax (the sum of its tax lines) is shared across its products in proportion to their subtotals. A return refunds the tax on what it returns: the order's tax times the returned amount divided by the order's products subtotal, rounded to 2 decimal places, halves rounding up. The return that completes the order (after it, every unit has been returned) refunds exactly the tax not refunded yet, so that the tax refunded always adds up to the order's tax.
- With "restock" true, each returned product's stock goes up by the quantity returned. With false, stock is unchanged.
- When every unit of the order has been returned, the order's status becomes REFUNDED. Until then it keeps its status.
- Every return adds an entry to the order's status history (GET /api/v1/private/orders/{id}/history), with the order's status after the return and a comment that names the amount refunded.
- Every return is recorded as a REFUND payment transaction for its amount, listed by GET /api/v1/private/orders/{id}/payment/transactions.
- The order, whenever it is returned by GET /api/v1/private/orders/{id}, has a line in "totals" with code "order.total.refunded" and the total refunded so far as a positive "value", once anything has been refunded. Its other totals don't change.

When you have finished, reply with one short paragraph saying what you changed.
