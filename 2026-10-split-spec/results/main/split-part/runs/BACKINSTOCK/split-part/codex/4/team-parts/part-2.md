# Part 2 — shopper and admin REST APIs

Implement the REST endpoints and request/response DTOs. Own files under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/**` and API-facing model/mapper files under `sm-shop/src/main/java/com/salesmanager/shop/model/**` that are specifically for stock alerts. Do not edit core persistence/service files or the inventory facade implementation owned by other parts.

Requirements (exact task wording):

- “Shopper API (no login needed, for the store given by ?store=):”
- “POST /api/v1/products/{sku}/alerts with {\"email\": \"...\"} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {\"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\"}.”
- “DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.”
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {\"id\": 1, \"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\" or \"SENT\", \"createdAt\": \"...\", \"sentAt\": null or \"...\"}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.”
- “GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {\"to\": \"<email>\", \"sku\": \"...\", \"subject\": \"<product name> is back in stock\", \"createdAt\": \"...\"}.”
- “An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”
- “A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.”
- “Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”

Use the project’s existing store resolution and private-endpoint security conventions. Map service exceptions to the specified status codes and preserve exact JSON field names/status values. Shopper endpoints must remain unauthenticated.

Other parts provide: Part 1 supplies the alert/outbox service and domain methods; call those rather than duplicating persistence. Part 3 supplies working inventory updates and invokes Part 1’s stock-transition hook.
