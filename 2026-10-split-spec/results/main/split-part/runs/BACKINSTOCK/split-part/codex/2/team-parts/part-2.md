# Part 2: shopper and admin REST APIs

## Scope and owned files

Own REST controllers, request/response DTOs and API-facing mappers under `sm-shop/src/main/java/com/salesmanager/shop/store/api/**` and `sm-shop-model/src/main/java/com/salesmanager/shop/model/stockalert/**` (plus adjacent API exception/config files only if required). Do not modify core alert persistence/service files owned by Part 1 or inventory facade/mapper files owned by Part 3.

## Requirements (exact task wording)

“Shopper API (no login needed, for the store given by ?store=):”

“- POST /api/v1/products/{sku}/alerts with {\"email\": \"...\"} asks to be told when the product is back in stock, and returns HTTP 201 with the alert: {\"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\"}.”

“- DELETE /api/v1/products/{sku}/alerts?email=... cancels that email's pending alert for the product, and returns HTTP 204.”

“Admin API (protected like the other /api/v1/private endpoints, for the store given by ?store=):”

“- GET /api/v1/private/stock-alerts lists the store's alerts, oldest first: {\"id\": 1, \"sku\": \"...\", \"email\": \"...\", \"status\": \"PENDING\" or \"SENT\", \"createdAt\": \"...\", \"sentAt\": null or \"...\"}. ?status=PENDING or ?status=SENT lists only those; any other status gives HTTP 400 Bad Request.”

“- GET /api/v1/private/stock-alerts/outbox lists the messages sent, oldest first: {\"to\": \"<email>\", \"sku\": \"...\", \"subject\": \"<product name> is back in stock\", \"createdAt\": \"...\"}.”

“An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”

“A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.”

“Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”

## Contract for other parts

Inject and call the Part 1 alert service methods (create/get pending, cancel, list/filter alerts, list outbox). Use the existing `MerchantStore`/`Language` argument resolver and security conventions so shopper routes are unauthenticated while `/private/**` routes are protected. Inventory transition behavior and dispatch are supplied by Part 3 calling Part 1; the API only serializes the resulting state.
