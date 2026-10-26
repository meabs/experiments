# Part 1: stock-alert domain and service

## Scope and owned files

Own the core persistence/model/service layer for stock alerts and the outbox. Add any new files under `sm-core-model/src/main/java/com/salesmanager/core/model/stockalert/**` and `sm-core/src/main/java/com/salesmanager/core/business/{repositories,services}/stockalert/**`. You may modify product deletion service/entity files in the core modules if needed to cascade/delete alerts, but do not modify `sm-shop` API/controller files or the inventory mapper/facade owned by Part 3.

## Requirements (exact task wording)

“Shoppers who find a product out of stock leave and do not come back. Let them ask to be told when it is back, and send those alerts when the store restocks it. Sending means recording the message in a store outbox that admins can read; no real email is sent.”

“An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”

“A missing or invalid email gives HTTP 400 Bad Request; an unknown sku gives HTTP 404 Not Found. Cancelling an alert that does not exist, or is already sent, gives HTTP 404 Not Found.”

“Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”

“When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”

“After a product sells out again, the same email can ask again, which makes a new pending alert.”

“A product with alerts can still be deleted as before, and its alerts go with it.”

## Contract for other parts

Expose a service interface/implementation with clear methods that Part 2 can call for shopper create/cancel and admin list operations (for example `createOrGetPending`, `cancel`, `listAlerts`, `listOutbox`). Expose a method Part 3 can call after an inventory update (for example `onInventoryQuantityChanged(Product product, int oldQuantity, int newQuantity)`), which only dispatches on a zero-to-positive transition. Return/domain objects must provide sku, email, status, id, createdAt, sentAt and outbox recipient/subject/createdAt values needed by the APIs. Scope all operations to the `MerchantStore`.
