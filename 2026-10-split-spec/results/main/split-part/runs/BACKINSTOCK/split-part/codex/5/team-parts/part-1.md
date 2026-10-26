# Part 1 — stock-alert domain and dispatch

## Scope

Implement the persistent stock-alert and outbox domain in `sm-core-model` and its repositories/services in `sm-core`. Add the service operation that inventory updates can call when quantity crosses from zero to positive, and ensure product deletion removes alerts with the product. Do not edit HTTP API classes or the shop inventory facade; Part 2 and Part 3 own those files.

## Files owned

- `sm-core-model/src/main/java/com/salesmanager/core/model/**` files needed for the alert and outbox entities and the Product relationship/cascade.
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/**` files for alert/outbox persistence.
- `sm-core/src/main/java/com/salesmanager/core/business/services/**` files for alert creation/cancellation/listing and restock dispatch.
- Any required Spring/JPA configuration or schema resource directly needed to make those core classes load.

## Requirements (exact task wording)

Shoppers who find a product out of stock leave and do not come back. Let them ask to be told when it is back, and send those alerts when the store restocks it. Sending means recording the message in a store outbox that admins can read; no real email is sent.

Rules:

- An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.
- A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.
- Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.
- When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.
- After a product sells out again, the same email can ask again, which makes a new pending alert.
- A product with alerts can still be deleted as before, and its alerts go with it.

## Contract with other parts

Expose a Spring bean/service with methods sufficient for Part 2 to create/cancel alerts and list alerts/outbox (including store + sku/email/status filtering), and for Part 3 to invoke restock dispatch with the product/store and old/new quantity. Use clear names such as `StockAlertService.createOrGetPending`, `cancelPending`, `list`, `listOutbox`, and `onStockUpdated` (the exact signatures may follow existing project conventions). Part 2 will map your domain objects to the required JSON. Part 3 will call the dispatch method only after a successful inventory save and provide the old and new quantities.

