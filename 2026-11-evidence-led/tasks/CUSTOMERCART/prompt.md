Shopping while logged in is broken in several ways, and logged-in customers are our best customers:

- A cart a logged-in customer fills (POST /api/v1/cart/ and PUT /api/v1/cart/{code} with their token) isn't linked to them. GET /api/v1/auth/customer/cart can't find it unless it is given the cart code, so the cart is lost when they come back on another device.
- Their cart total, GET /api/v1/auth/cart/{id}/total, fails with HTTP 503.
- When logged-in checkout (POST /api/v1/auth/cart/{code}/checkout) is sent a payment amount that doesn't match the order, it fails with HTTP 503 instead of saying what the amount should be, the way guest checkout does.
- GET /api/v1/auth/orders lists the customer's orders but reports "recordsTotal" 0 and "totalPages" 0.

Make logged-in shopping work:

- A cart created or changed with a customer's token belongs to that customer. GET /api/v1/auth/customer/cart, without a cart parameter, returns their current cart: the one they most recently created or changed that hasn't been checked out. If they have none, it gives HTTP 404 Not Found. A customer never gets another customer's cart.
- GET /api/v1/auth/cart/{id}/total returns the totals of the customer's cart, with tax worked out for the customer's delivery address: the same subtotal, tax and total that checkout will charge. Another customer's cart gives HTTP 404 Not Found.
- Logged-in checkout with a payment amount that doesn't match the order gives HTTP 400 Bad Request, with a message that names the amount the order costs, as guest checkout does; nothing is ordered. With the right amount it succeeds, and the cart is then no longer the customer's current cart.
- GET /api/v1/auth/orders lists only the customer's own orders, newest first, with "recordsTotal" the number of their orders and "totalPages" the number of pages for the page size asked for with "count".

When you have finished, reply with one short paragraph saying what you changed.
