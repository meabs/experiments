Part 2 – shopper and admin stock-alert APIs

Own these files and new files in the corresponding shop packages: sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/; sm-shop/src/main/java/com/salesmanager/shop/store/controller/; sm-shop/src/main/java/com/salesmanager/shop/store/facade/; sm-shop/src/main/java/com/salesmanager/shop/model/; plus mappers/exception handling needed for these endpoints. Do not edit core/model files owned by Part 1 or inventory files owned by Part 3.

Build shopper endpoints (no login) and protected admin endpoints, using the existing MerchantStore argument/security conventions. Validate email and map unknown SKU, in-stock, duplicate, and cancellation outcomes to required HTTP statuses. Admin list ordering is oldest first and status filtering is strict.

Requirements from TASK.md applying here:

- “Shopper API (no login needed, for the store given by ?store=):”
- “POST /api/v1/products/{sku}/alerts with {\"email\": \"...\"} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {\"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\"}.”
- “DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.”
- “Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”
- “GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {\"id\": 1, \"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\" or \"SENT\", \"createdAt\": \"...\", \"sentAt\": null or \"...\"}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.”
- “GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {\"to\": \"<email>\", \"sku\": \"...\", \"subject\": \"<product name> is back in stock\", \"createdAt\": \"...\"}.”
- “A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.”

Part 1 provides the alert/outbox service and domain methods; use those rather than duplicating persistence. Part 3 provides working inventory transitions and calls Part 1 processing.
