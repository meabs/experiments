Shoppers who find a product out of stock leave and do not come back. Let them ask to be told when it is back, and send those alerts when the store restocks it. Sending means recording the message in a store outbox that admins can read; no real email is sent.

Shopper API (no login needed, for the store given by ?store=):

- POST /api/v1/products/{sku}/alerts with {"email": "..."} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {"sku": "...", "email": "...", "status": "PENDING"}.
- DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.

Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):

- GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {"id": 1, "sku": "...", "email": "...", "status": "PENDING" or "SENT", "createdAt": "...", "sentAt": null or "..."}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.
- GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {"to": "<email>", "sku": "...", "subject": "<product name> is back in stock", "createdAt": "..."}.

Rules:

- An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.
- A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.
- Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.
- When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.
- After a product sells out again, the same email can ask again, which makes a new pending alert.
- Admins change stock with the existing inventory API: PUT /api/v1/private/product/{productId}/inventory/{inventoryId} with {"productId": ..., "quantity": ..., "available": true}, where the inventory id comes from GET /api/v1/private/product/{sku}/inventory. Today that update fails with an error for products created through the product API, and when no prices are given; it must work, and an update without prices keeps the existing prices.
- A product with alerts can still be deleted as before, and its alerts go with it.
