# Part 1 — stock-alert domain and persistence

Implement the stock-alert and outbox domain, persistence, and service logic. Own files under `sm-core-model/src/main/java/**` for alert/outbox model classes, and under `sm-core/src/main/java/com/salesmanager/core/business/{repositories,services}/stockalert/**` (plus closely corresponding mapping/config files only if required). Do not edit API controllers or inventory facade files owned by other parts.

Requirements (exact task wording):

- “Shoppers who find a product out of stock leave and do not come back. Let them ask to be told when it is back, and send those alerts when the store restocks it. Sending means recording the message in a store outbox that admins can read; no real email is sent.”
- “An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.”
- “Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.”
- “When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, \"sentAt\" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.”
- “After a product sells out again, the same email can ask again, which makes a new pending alert.”
- “A product with alerts can still be deleted as before, and its alerts go with it.”

Provide a service with clear methods for create/find-pending/cancel/list and a stock-transition method (for example `onStockUpdated(Product, oldQuantity, newQuantity)`), plus DTO-readable data needed by the API part. Scope alerts by merchant store and SKU/product; preserve timestamps and oldest-first ordering. Use existing project persistence conventions and cascade/delete behavior.

Other parts provide: Part 2 will call your alert service from shopper/admin controllers (use the service/class/method names you expose); Part 3 will invoke your stock-transition method after a successful inventory update and will handle inventory update compatibility fixes.
