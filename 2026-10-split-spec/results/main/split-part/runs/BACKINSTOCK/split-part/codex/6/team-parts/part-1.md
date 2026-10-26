Implement the stock-alert domain and persistence/service layer.

Files owned:
- sm-core-model/src/main/java/com/salesmanager/core/model/catalog/product/stockalert/** (new alert and outbox entities/enums as needed)
- sm-core/src/main/java/com/salesmanager/core/business/repositories/catalog/product/stockalert/** (repositories)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/stockalert/** (service interface/implementation)
- sm-core/src/main/java/com/salesmanager/core/business/services/catalog/product/ProductServiceImpl.java only where needed to remove alerts/outbox when a product is deleted

Requirements (exact task wording):
Shoppers who find a product out of stock leave and do not come back. Let them ask to be told when it is back, and send those alerts when the store restocks it. Sending means recording the message in a store outbox that admins can read; no real email is sent.

- An alert can only be made for a product with no stock; a product in stock gives HTTP 409 Conflict.
- Emails match ignoring case. Asking again with an email that already has a pending alert for the product changes nothing and returns HTTP 200 with that alert.
- When an admin raises a product's stock from zero to more than zero, every pending alert for that product is sent at once: its status becomes SENT, "sentAt" is set, and one message per alert is added to the outbox. Alerts for other products stay pending. Changing stock that stays at zero, or raising stock that is already above zero, sends nothing; each alert is sent only once.
- After a product sells out again, the same email can ask again, which makes a new pending alert.
- A product with alerts can still be deleted as before, and its alerts go with it.

Provide a service with clear methods for creating/idempotently finding pending alerts, cancelling pending alerts, listing alerts by store/status, listing outbox messages, and processing a zero-to-positive stock transition. Use the existing Product, MerchantStore, and ProductAvailability relationships and timestamps. Expose class/method names in a stable way for the shop facade and inventory facade to call (for example StockAlertService.createOrGetPending(...), cancelPending(...), list(...), listOutbox(...), notifyRestocked(...)).

Other parts provide:
- Part 2 will adapt this service to shopper/admin HTTP resources and DTOs.
- Part 3 will call the stock-transition method from ProductInventoryFacadeImpl after a successful inventory update, passing the product and old/new quantities.
